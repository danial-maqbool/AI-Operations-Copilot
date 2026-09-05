export interface MetricSnapshot {
  id: string;
  name: string;
  code: string;
  current_value: number;
  previous_value: number;
  pct_change: number;
  status: 'GOOD' | 'WARNING' | 'CRITICAL';
  owner: string;
  target_value?: number;
  sparkline: { label: string; value: number }[];
}

export interface ExceptionItem {
  id: string;
  rule_id?: string;
  exception_type: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  entity_type: string;
  entity_id: string;
  title: string;
  description?: string;
  financial_impact: number;
  age_days: number;
  priority_score: number;
  status: 'OPEN' | 'ACKNOWLEDGED' | 'RESOLVED' | 'IGNORED';
  evidence?: any;
  created_at?: string;
}

export interface ActionItem {
  id: string;
  exception_id?: string;
  title: string;
  description?: string;
  reason?: string;
  priority: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  owner: string;
  action_type: 'create_task' | 'export_csv' | 'draft_email' | 'call_list' | 'status_update';
  status: 'PROPOSED' | 'APPROVED' | 'IN_PROGRESS' | 'COMPLETED' | 'REJECTED';
  rejection_reason?: string;
  approved_by?: string;
  due_date?: string;
  suggested_steps: string[];
  affected_records: any[];
  execution_result?: any;
}

export interface ColumnProfile {
  id: string;
  table_name: string;
  column_name: string;
  data_type: string;
  inferred_role: string;
  user_role_override?: string;
  inferred_description?: string;
  user_description_override?: string;
  null_count: number;
  null_percentage: number;
  unique_count: number;
  sample_values: any[];
  is_primary_key: boolean;
  is_foreign_key: boolean;
  is_sensitive: boolean;
}

export interface TableProfile {
  id: string;
  table_name: string;
  row_count: number;
  column_count: number;
  missing_cells_total: number;
  duplicate_rows: number;
  detected_entity: string;
  data_health_score: number;
  columns: ColumnProfile[];
}

export interface WorkflowRun {
  id: string;
  workflow_id: string;
  status: string;
  started_at: string;
  completed_at?: string;
  records_processed: number;
  actions_created: number;
  error_message?: string;
  execution_log: any[];
}

export interface Workflow {
  id: string;
  name: string;
  description?: string;
  trigger_type: string;
  steps: any[];
  is_active: boolean;
  runs: WorkflowRun[];
}

export interface DocumentItem {
  id: string;
  filename: string;
  file_type: string;
  total_pages: number;
  total_chunks: number;
  status: string;
  uploaded_at: string;
}

export interface SearchCitation {
  document_id: string;
  filename: string;
  page_number: number;
  section_title?: string;
  content: string;
  score: number;
  citation: string;
}

export interface CopilotResponse {
  conversation_id: string;
  message_id: string;
  direct_answer: string;
  confidence: string;
  data_used: string[];
  filters_applied: string[];
  calculations: Record<string, any>;
  table_data?: {
    columns: string[];
    rows: any[][];
    total_rows: number;
  };
  chart?: {
    chart_type: string;
    title: string;
    x_axis: string;
    y_axis: string;
    series: { name: string; value: number }[];
  };
  sql_queries: string[];
  policy_citations: string[];
  recommended_actions: any[];
  tools_executed: string[];
  evidence: any;
}

export interface MorningReviewData {
  review_id: string;
  timestamp: string;
  data_health_score: number;
  kpi_summary: {
    total_kpis: number;
    counts: Record<string, number>;
    kpis: MetricSnapshot[];
  };
  exceptions_summary: {
    total_open: number;
    severity_counts: Record<string, number>;
    total_financial_impact: number;
    top_exceptions: any[];
  };
  sla_summary: {
    total_monitored: number;
    breached_count: number;
    at_risk_count: number;
    safe_count: number;
    financial_exposure: number;
  };
  anomalies_summary: {
    total_detected: number;
    items: any[];
  };
  todays_prioritized_actions: any[];
  executive_brief: string;
  duration_ms: number;
}
