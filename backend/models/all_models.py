import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from backend.database import Base

def gen_uuid():
    return str(uuid.uuid4())

class Workspace(Base):
    __tablename__ = "workspaces"
    
    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(100), nullable=False, default="Default Workspace")
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DataSource(Base):
    __tablename__ = "data_sources"
    
    id = Column(String(36), primary_key=True, default=gen_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False)
    name = Column(String(100), nullable=False)
    source_type = Column(String(30), nullable=False)  # csv, excel, json, sqlite, postgres
    connection_uri = Column(Text, nullable=True)
    file_path = Column(Text, nullable=True)
    status = Column(String(30), default="connected")  # connected, disconnected, error
    row_count = Column(Integer, default=0)
    table_count = Column(Integer, default=0)
    last_refreshed = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    tables = relationship("DataSourceTable", back_populates="data_source", cascade="all, delete-orphan")

class DataSourceTable(Base):
    __tablename__ = "data_source_tables"
    
    id = Column(String(36), primary_key=True, default=gen_uuid)
    data_source_id = Column(String(36), ForeignKey("data_sources.id"), nullable=False)
    table_name = Column(String(100), nullable=False)
    row_count = Column(Integer, default=0)
    column_count = Column(Integer, default=0)
    sheet_name = Column(String(100), nullable=True)
    file_path = Column(Text, nullable=True)
    schema_metadata = Column(JSON, default=dict)
    data_health_score = Column(Float, default=100.0)
    health_metrics = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    data_source = relationship("DataSource", back_populates="tables")
    columns = relationship("DataCatalogColumn", back_populates="table", cascade="all, delete-orphan")

class DataCatalogColumn(Base):
    __tablename__ = "data_catalog_columns"
    
    id = Column(String(36), primary_key=True, default=gen_uuid)
    table_id = Column(String(36), ForeignKey("data_source_tables.id"), nullable=False)
    column_name = Column(String(100), nullable=False)
    data_type = Column(String(50), nullable=False)
    inferred_role = Column(String(50), default="category")  # identifier, business_date, category, metric, status, sensitive
    user_role_override = Column(String(50), nullable=True)
    inferred_description = Column(Text, nullable=True)
    user_description_override = Column(Text, nullable=True)
    null_count = Column(Integer, default=0)
    null_percentage = Column(Float, default=0.0)
    unique_count = Column(Integer, default=0)
    sample_values = Column(JSON, default=list)
    is_primary_key = Column(Boolean, default=False)
    is_foreign_key = Column(Boolean, default=False)
    is_sensitive = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    table = relationship("DataSourceTable", back_populates="columns")

class Relationship(Base):
    __tablename__ = "relationships"
    
    id = Column(String(36), primary_key=True, default=gen_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False)
    source_table_name = Column(String(100), nullable=False)
    source_column_name = Column(String(100), nullable=False)
    target_table_name = Column(String(100), nullable=False)
    target_column_name = Column(String(100), nullable=False)
    confidence_score = Column(Float, default=0.9)
    detection_method = Column(String(50), default="name_heuristic")
    is_verified = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Metric(Base):
    __tablename__ = "metrics"
    
    id = Column(String(36), primary_key=True, default=gen_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False)
    name = Column(String(100), nullable=False)
    code = Column(String(50), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    source_table = Column(String(100), nullable=False)
    formula = Column(Text, nullable=False)  # e.g., COUNT(*), SUM(amount), AVG(duration)
    time_column = Column(String(100), nullable=True)
    aggregation = Column(String(30), default="sum")
    target_value = Column(Float, nullable=True)
    warning_threshold = Column(Float, nullable=True)
    critical_threshold = Column(Float, nullable=True)
    comparison_direction = Column(String(30), default="higher_is_better")  # higher_is_better, lower_is_better
    owner = Column(String(100), default="Operations Team")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    snapshots = relationship("MetricSnapshot", back_populates="metric", cascade="all, delete-orphan")

class MetricSnapshot(Base):
    __tablename__ = "metric_snapshots"
    
    id = Column(String(36), primary_key=True, default=gen_uuid)
    metric_id = Column(String(36), ForeignKey("metrics.id"), nullable=False)
    period_label = Column(String(50), default="Current")
    current_value = Column(Float, default=0.0)
    previous_value = Column(Float, default=0.0)
    pct_change = Column(Float, default=0.0)
    status = Column(String(20), default="GOOD")  # GOOD, WARNING, CRITICAL
    sparkline_data = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    metric = relationship("Metric", back_populates="snapshots")

class BusinessRule(Base):
    __tablename__ = "rules"
    
    id = Column(String(36), primary_key=True, default=gen_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False)
    name = Column(String(100), nullable=False)
    entity = Column(String(50), nullable=False)  # orders, invoices, tickets, inventory, etc.
    target_table = Column(String(100), nullable=False)
    conditions = Column(JSON, default=list)  # list of {field, operator, value}
    severity = Column(String(20), default="HIGH")  # INFO, WARNING, CRITICAL
    action_template = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class OperationsException(Base):
    __tablename__ = "exceptions"
    
    id = Column(String(36), primary_key=True, default=gen_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False)
    rule_id = Column(String(36), ForeignKey("rules.id"), nullable=True)
    exception_type = Column(String(50), nullable=False)  # overdue_invoice, late_shipment, low_stock, sla_risk
    severity = Column(String(20), default="HIGH")  # LOW, MEDIUM, HIGH, CRITICAL
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(100), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    observed_value = Column(String(100), nullable=True)
    financial_impact = Column(Float, default=0.0)
    sla_deadline = Column(DateTime, nullable=True)
    owner = Column(String(100), default="Operations Lead")
    age_days = Column(Integer, default=0)
    priority_score = Column(Float, default=50.0)
    status = Column(String(30), default="OPEN")  # OPEN, ACKNOWLEDGED, RESOLVED, IGNORED
    evidence = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ActionItem(Base):
    __tablename__ = "actions"
    
    id = Column(String(36), primary_key=True, default=gen_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False)
    exception_id = Column(String(36), ForeignKey("exceptions.id"), nullable=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    reason = Column(Text, nullable=True)
    source_finding = Column(Text, nullable=True)
    priority = Column(String(20), default="HIGH")  # LOW, MEDIUM, HIGH, CRITICAL
    owner = Column(String(100), default="Operations Manager")
    due_date = Column(DateTime, nullable=True)
    suggested_steps = Column(JSON, default=list)
    affected_records = Column(JSON, default=list)
    action_type = Column(String(50), default="create_task")  # create_task, export_csv, draft_email, call_list, status_update
    status = Column(String(30), default="PROPOSED")  # PROPOSED, APPROVED, IN_PROGRESS, COMPLETED, REJECTED
    rejection_reason = Column(Text, nullable=True)
    approval_required = Column(Boolean, default=True)
    approved_by = Column(String(100), nullable=True)
    executed_at = Column(DateTime, nullable=True)
    execution_result = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Workflow(Base):
    __tablename__ = "workflows"
    
    id = Column(String(36), primary_key=True, default=gen_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    trigger_type = Column(String(50), default="manual")  # manual, schedule, threshold
    steps = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    runs = relationship("WorkflowRun", back_populates="workflow", cascade="all, delete-orphan")

class WorkflowRun(Base):
    __tablename__ = "workflow_runs"
    
    id = Column(String(36), primary_key=True, default=gen_uuid)
    workflow_id = Column(String(36), ForeignKey("workflows.id"), nullable=False)
    status = Column(String(30), default="RUNNING")  # RUNNING, COMPLETED, FAILED
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    records_processed = Column(Integer, default=0)
    actions_created = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    execution_log = Column(JSON, default=list)
    
    workflow = relationship("Workflow", back_populates="runs")

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(String(36), primary_key=True, default=gen_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False)
    filename = Column(String(200), nullable=False)
    file_type = Column(String(20), nullable=False)  # pdf, docx, txt, md
    file_path = Column(Text, nullable=False)
    total_pages = Column(Integer, default=1)
    total_chunks = Column(Integer, default=0)
    status = Column(String(30), default="INDEXED")
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    
    id = Column(String(36), primary_key=True, default=gen_uuid)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(Integer, default=0)
    page_number = Column(Integer, default=1)
    section_title = Column(String(200), nullable=True)
    content = Column(Text, nullable=False)
    token_count = Column(Integer, default=0)
    embedding_vector = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    document = relationship("Document", back_populates="chunks")

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(String(36), primary_key=True, default=gen_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False)
    title = Column(String(200), default="Operations Conversation")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(String(36), primary_key=True, default=gen_uuid)
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    evidence = Column(JSON, default=dict)
    confidence = Column(String(20), default="HIGH")  # HIGH, MEDIUM, LOW
    suggested_actions = Column(JSON, default=list)
    sql_queries = Column(JSON, default=list)
    charts = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    conversation = relationship("Conversation", back_populates="messages")
    tool_calls = relationship("ToolCall", back_populates="message", cascade="all, delete-orphan")

class ToolCall(Base):
    __tablename__ = "tool_calls"
    
    id = Column(String(36), primary_key=True, default=gen_uuid)
    message_id = Column(String(36), ForeignKey("messages.id"), nullable=False)
    tool_name = Column(String(100), nullable=False)
    arguments = Column(JSON, default=dict)
    result = Column(JSON, default=dict)
    duration_ms = Column(Integer, default=0)
    status = Column(String(30), default="SUCCESS")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    message = relationship("Message", back_populates="tool_calls")

class SavedAnalysis(Base):
    __tablename__ = "saved_analyses"
    
    id = Column(String(36), primary_key=True, default=gen_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False)
    title = Column(String(200), nullable=False)
    question = Column(Text, nullable=False)
    sql_query = Column(Text, nullable=True)
    chart_config = Column(JSON, default=dict)
    last_run_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

class Report(Base):
    __tablename__ = "reports"
    
    id = Column(String(36), primary_key=True, default=gen_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False)
    title = Column(String(200), nullable=False)
    period = Column(String(50), default="Weekly")
    report_type = Column(String(50), default="EXECUTIVE")
    sections = Column(JSON, default=dict)
    export_formats = Column(JSON, default=lambda: ["json", "csv", "xlsx"])
    file_path = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditEvent(Base):
    __tablename__ = "audit_events"
    
    id = Column(String(36), primary_key=True, default=gen_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False)
    event_type = Column(String(100), nullable=False)  # user_question, tool_execution, sql_executed, action_proposed, action_approved, action_rejected, action_executed, workflow_run
    user_name = Column(String(100), default="System")
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(String(100), nullable=True)
    details = Column(JSON, default=dict)
    status = Column(String(20), default="SUCCESS")
    created_at = Column(DateTime, default=datetime.utcnow)
