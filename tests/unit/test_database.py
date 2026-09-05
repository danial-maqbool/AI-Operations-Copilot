import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database import Base
from backend.models import (
    Workspace, DataSource, DataSourceTable, DataCatalogColumn,
    Relationship, Metric, BusinessRule, OperationsException,
    ActionItem, Workflow, Document, Conversation, Report, AuditEvent
)

@pytest.fixture
def db_session():
    test_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=test_engine)
    Session = sessionmaker(bind=test_engine)
    session = Session()
    yield session
    session.close()

def test_models_creation(db_session):
    # 1. Create Workspace
    ws = Workspace(name="Test Corp", description="Operations testing")
    db_session.add(ws)
    db_session.commit()
    assert ws.id is not None
    
    # 2. Create DataSource
    ds = DataSource(workspace_id=ws.id, name="ERP SQLite", source_type="sqlite")
    db_session.add(ds)
    db_session.commit()
    assert ds.id is not None
    
    # 3. Create Table & Columns
    table = DataSourceTable(data_source_id=ds.id, table_name="orders", row_count=100)
    db_session.add(table)
    db_session.commit()
    
    col = DataCatalogColumn(table_id=table.id, column_name="order_id", data_type="INTEGER", is_primary_key=True)
    db_session.add(col)
    db_session.commit()
    assert col.id is not None
    
    # 4. Create Metric
    metric = Metric(workspace_id=ws.id, name="Total Revenue", code="REV", source_table="orders", formula="SUM(amount)")
    db_session.add(metric)
    db_session.commit()
    assert metric.id is not None
    
    # 5. Create Business Rule
    rule = BusinessRule(workspace_id=ws.id, name="Overdue Invoices", entity="invoices", target_table="invoices")
    db_session.add(rule)
    db_session.commit()
    
    # 6. Create Operations Exception & Action Item
    exc = OperationsException(
        workspace_id=ws.id, rule_id=rule.id, exception_type="overdue_invoice",
        severity="HIGH", entity_type="invoice", entity_id="INV-001",
        title="Overdue Invoice INV-001"
    )
    db_session.add(exc)
    db_session.commit()
    
    action = ActionItem(
        workspace_id=ws.id, exception_id=exc.id, title="Follow up with client",
        priority="HIGH", status="PROPOSED"
    )
    db_session.add(action)
    db_session.commit()
    assert action.id is not None
    assert action.status == "PROPOSED"
    
    # 7. Audit Event
    audit = AuditEvent(workspace_id=ws.id, event_type="action_proposed", entity_id=action.id)
    db_session.add(audit)
    db_session.commit()
    assert audit.id is not None
