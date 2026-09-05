const BASE_URL = import.meta.env.VITE_API_URL || '';

export const api = {
  // Demo Data
  async loadDemoCompany() {
    const res = await fetch(`${BASE_URL}/api/demo/load`, { method: 'POST' });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  // Morning Review
  async runMorningReview() {
    const res = await fetch(`${BASE_URL}/api/morning-review/run`, { method: 'POST' });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async getLatestMorningReview() {
    const res = await fetch(`${BASE_URL}/api/morning-review/latest`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  // Copilot Chat
  async sendCopilotMessage(question: string, conversationId?: string) {
    const res = await fetch(`${BASE_URL}/api/copilot/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, conversation_id: conversationId })
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  // Data Sources & Catalog
  async getDataSources() {
    const res = await fetch(`${BASE_URL}/api/data-sources`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async getCatalogTables() {
    const res = await fetch(`${BASE_URL}/api/catalog/tables`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async updateColumnOverride(columnId: string, override: { user_role_override?: string; user_description_override?: string; is_sensitive?: boolean }) {
    const res = await fetch(`${BASE_URL}/api/catalog/columns/${columnId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(override)
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  // Metrics
  async getMetrics() {
    const res = await fetch(`${BASE_URL}/api/metrics`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async testMetricFormula(sourceTable: string, formula: string) {
    const res = await fetch(`${BASE_URL}/api/metrics/test-formula`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source_table: sourceTable, formula })
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  // Exceptions & SLA
  async getExceptions() {
    const res = await fetch(`${BASE_URL}/api/exceptions`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async updateExceptionStatus(id: string, status: string) {
    const res = await fetch(`${BASE_URL}/api/exceptions/${id}/status`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status })
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async getSLAMonitor() {
    const res = await fetch(`${BASE_URL}/api/entities/sla-monitor`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async getCustomer360(customerId: string) {
    const res = await fetch(`${BASE_URL}/api/entities/customer/${customerId}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  // Action Center
  async getActions(status?: string) {
    const url = status ? `${BASE_URL}/api/actions?status=${status}` : `${BASE_URL}/api/actions`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async approveAction(id: string, approvedBy: string = 'Operations Lead') {
    const res = await fetch(`${BASE_URL}/api/actions/${id}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'approve', approved_by: approvedBy })
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async rejectAction(id: string, rejectionReason: string, approvedBy: string = 'Operations Lead') {
    const res = await fetch(`${BASE_URL}/api/actions/${id}/reject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'reject', rejection_reason: rejectionReason, approved_by: approvedBy })
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async executeAction(id: string) {
    const res = await fetch(`${BASE_URL}/api/actions/${id}/execute`, { method: 'POST' });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  // Workflows
  async getWorkflows() {
    const res = await fetch(`${BASE_URL}/api/workflows`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async runWorkflow(id: string) {
    const res = await fetch(`${BASE_URL}/api/workflows/${id}/run`, { method: 'POST' });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  // Documents & RAG
  async getDocuments() {
    const res = await fetch(`${BASE_URL}/api/documents`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async searchDocuments(query: string) {
    const res = await fetch(`${BASE_URL}/api/documents/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, top_k: 5 })
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  // Reports
  async getReports() {
    const res = await fetch(`${BASE_URL}/api/reports`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async generateReport(payload: { title: string; period: string; report_type: string }) {
    const res = await fetch(`${BASE_URL}/api/reports/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  // Audit
  async getAuditLog(limit: number = 50) {
    const res = await fetch(`${BASE_URL}/api/audit?limit=${limit}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async getAuditStats() {
    const res = await fetch(`${BASE_URL}/api/audit/stats`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  // Safe SQL Query runner
  async executeSQL(sql: string) {
    const res = await fetch(`${BASE_URL}/api/queries/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sql })
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  }
};
