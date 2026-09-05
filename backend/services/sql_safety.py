import time
import re
import sqlite3
import pandas as pd
import numpy as np
import sqlglot
import sqlglot.expressions as exp
from typing import List, Dict, Any, Optional, Tuple

from backend.config import settings
from backend.services.warehouse import get_warehouse_tables, WAREHOUSE_PATH

class SQLSafetyError(Exception):
    pass

class SQLSafetyValidator:
    FORBIDDEN_EXPRESSIONS = (
        exp.Insert, exp.Update, exp.Delete, exp.Drop,
        exp.Alter, exp.Create, exp.TruncateTable, exp.Command,
        exp.Grant, exp.Revoke, exp.Pragma
    )
    
    FORBIDDEN_RAW_WORDS = [
        "DROP ", "DELETE ", "INSERT ", "UPDATE ", "ALTER ", "TRUNCATE ", 
        "CREATE ", "REPLACE ", "ATTACH ", "DETACH ", "PRAGMA ", "VACUUM "
    ]

    @classmethod
    def sanitize_and_parse(cls, sql: str) -> exp.Expression:
        clean_sql = sql.strip()
        if not clean_sql:
            raise SQLSafetyError("Empty query provided")

        # Check for dangerous keywords at start of statement
        upper_raw = clean_sql.upper()
        for bad in cls.FORBIDDEN_RAW_WORDS:
            if upper_raw.startswith(bad) or f";{bad}" in upper_raw or f"; {bad}" in upper_raw:
                raise SQLSafetyError(f"Prohibited write/DDL operation: '{bad.strip()}' is not permitted in read-only mode")

        # Parse AST with sqlglot
        try:
            parsed_list = sqlglot.parse(clean_sql, read="sqlite")
        except Exception as e:
            raise SQLSafetyError(f"SQL Syntax Error: {str(e)}")

        # Check multi-statement rejection
        valid_statements = [p for p in parsed_list if p is not None]
        if len(valid_statements) == 0:
            raise SQLSafetyError("No valid SQL statements found")
        if len(valid_statements) > 1:
            raise SQLSafetyError("Execution of multiple statements is strictly blocked for security")

        root = valid_statements[0]

        # Check forbidden AST nodes anywhere in expression tree
        for node in root.walk():
            if isinstance(node, cls.FORBIDDEN_EXPRESSIONS):
                raise SQLSafetyError(f"Prohibited operation AST node '{type(node).__name__}' detected. Only read-only queries are permitted.")

        # Check root expression is Select or Union
        if not isinstance(root, (exp.Select, exp.Union)):
            # Allow explain queries if parsed
            if not upper_raw.startswith("EXPLAIN"):
                raise SQLSafetyError(f"Root statement type '{type(root).__name__}' is not allowed. Must be a SELECT query.")

        return root

    @classmethod
    def extract_referenced_tables(cls, expression: exp.Expression) -> List[str]:
        # Collect CTE aliases to exclude them from external table checking
        cte_aliases = set()
        for with_clause in expression.find_all(exp.With):
            for cte in with_clause.expressions:
                if cte.alias:
                    cte_aliases.add(cte.alias.lower())

        # Collect table nodes
        tables = set()
        for table_node in expression.find_all(exp.Table):
            t_name = table_node.name.lower()
            if t_name and t_name not in cte_aliases:
                tables.add(t_name)

        return sorted(list(tables))

    @classmethod
    def enforce_limit(cls, expression: exp.Expression, max_limit: int = 500) -> exp.Expression:
        # Check if query has a limit clause
        limit_node = expression.find(exp.Limit)
        if limit_node:
            try:
                curr_limit = int(limit_node.expression.this)
                if curr_limit > max_limit:
                    limit_node.set("this", exp.Literal.number(max_limit))
            except Exception:
                limit_node.set("this", exp.Literal.number(max_limit))
        else:
            # Append LIMIT clause
            expression = expression.limit(max_limit)
        return expression

    @classmethod
    def generate_explanation(cls, expression: exp.Expression, tables: List[str]) -> str:
        parts = []
        table_list = ", ".join([f"'{t}'" for t in tables]) if tables else "operational tables"
        parts.append(f"Queries data from {table_list}")

        # Check WHERE clause
        where_clause = expression.find(exp.Where)
        if where_clause:
            cond_str = where_clause.this.sql(dialect="sqlite")
            parts.append(f"filters rows by {cond_str}")

        # Check GROUP BY
        group_clause = expression.find(exp.Group)
        if group_clause:
            cols = [e.sql(dialect="sqlite") for e in group_clause.expressions]
            parts.append(f"aggregates records by {', '.join(cols)}")

        # Check ORDER BY
        order_clause = expression.find(exp.Order)
        if order_clause:
            orders = [e.sql(dialect="sqlite") for e in order_clause.expressions]
            parts.append(f"orders results by {', '.join(orders)}")

        # Check LIMIT
        limit_clause = expression.find(exp.Limit)
        if limit_clause:
            parts.append(f"caps output to {limit_clause.expression.this} records")

        return "The query " + ", and ".join(parts) + "."

    @classmethod
    def validate_and_sanitize(cls, sql: str, allowed_tables: Optional[List[str]] = None) -> Tuple[str, List[str], str]:
        root = cls.sanitize_and_parse(sql)
        tables = cls.extract_referenced_tables(root)

        # Validate against allowed tables if specified, otherwise against warehouse tables
        available_tables = [t.lower() for t in (allowed_tables or get_warehouse_tables())]
        for t in tables:
            if t not in available_tables:
                raise SQLSafetyError(f"Referenced table '{t}' does not exist in the active data sources")

        # Enforce max row limit
        max_rows = getattr(settings, "MAX_DISPLAYED_ROWS", 500)
        bounded_expr = cls.enforce_limit(root, max_limit=max_rows)
        sanitized_sql = bounded_expr.sql(dialect="sqlite")
        explanation = cls.generate_explanation(bounded_expr, tables)

        return sanitized_sql, tables, explanation

    @classmethod
    def validate_query(cls, sql: str, allowed_tables: Optional[List[str]] = None) -> Tuple[str, str]:
        safe_sql, tables, explanation = cls.validate_and_sanitize(sql, allowed_tables)
        return safe_sql, explanation

    @classmethod
    def execute_safe_query(cls, sql: str, allowed_tables: Optional[List[str]] = None) -> Dict[str, Any]:
        start_time = time.time()
        sanitized_sql, tables, explanation = cls.validate_and_sanitize(sql, allowed_tables)

        # Execute query against SQLite warehouse with timeout protection
        conn = sqlite3.connect(str(WAREHOUSE_PATH), timeout=float(settings.MAX_QUERY_SECONDS))
        try:
            cursor = conn.cursor()
            cursor.execute(sanitized_sql)
            col_names = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            
            # Build clean records list handling NaN/Inf/None
            records = []
            for r in rows:
                row_dict = {}
                for idx, col in enumerate(col_names):
                    val = r[idx]
                    if isinstance(val, float) and (np.isnan(val) or np.isinf(val)):
                        val = None
                    row_dict[col] = val
                records.append(row_dict)

            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            return {
                "success": True,
                "sql": sql,
                "sanitized_sql": sanitized_sql,
                "explanation": explanation,
                "columns": col_names,
                "rows": records,
                "total_rows": len(records),
                "duration_ms": elapsed_ms,
                "referenced_tables": tables,
                "error": None
            }
        except Exception as e:
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            return {
                "success": False,
                "sql": sql,
                "sanitized_sql": sanitized_sql,
                "explanation": explanation,
                "columns": [],
                "rows": [],
                "total_rows": 0,
                "duration_ms": elapsed_ms,
                "referenced_tables": tables,
                "error": str(e)
            }
        finally:
            conn.close()

SafeSQLEngine = SQLSafetyValidator

