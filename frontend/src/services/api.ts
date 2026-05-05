// API service for communicating with backend
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export interface Application {
  full_name: string;
  email: string;
  phone: string;
  date_of_birth: string;
  gender: string;
  street_address: string;
  city: string;
  state: string;
  postal_code: string;
  country: string;
  annual_income: number;
  monthly_expenses: number;
  employment_status: string;
  years_employed: number;
  employer: string;
  credit_score: number;
  existing_debts: number;
  number_of_accounts: number;
  delinquencies: number;
  loan_amount: number;
  loan_term_months: number;
  loan_purpose: string;
  collateral_value?: number;
  applicant_notes?: string;
  additional_data?: any;
}

export interface Decision {
  id: number;
  application_id: number;
  decision: 'approved' | 'rejected' | 'conditional' | 'pending';
  confidence: number;
  risk_score: number;
  reasoning: string;
  explanation: string;
  model_used: string;
  latency_ms: number;
  total_tokens_used: number;
  estimated_cost: number;
  rag_used: boolean;
  created_at: string;
  feedback?: 'correct' | 'incorrect';
}

export const apiService = {
  // Health check
  async healthCheck() {
    const response = await fetch(`${API_URL}/health`);
    return response.json();
  },

  // Applications
  async createApplication(appData: Application) {
    const response = await fetch(`${API_URL}/applications`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(appData),
    });
    if (!response.ok) throw new Error('Failed to create application');
    return response.json();
  },

  async getApplication(applicationId: number) {
    const response = await fetch(`${API_URL}/applications/${applicationId}`);
    if (!response.ok) throw new Error('Failed to get application');
    return response.json();
  },

  async listApplications(skip = 0, limit = 100) {
    const response = await fetch(
      `${API_URL}/applications?skip=${skip}&limit=${limit}`
    );
    if (!response.ok) throw new Error('Failed to list applications');
    return response.json();
  },

  // Decisions
  async underwrite(appData: Application, forceModel?: string) {
    const response = await fetch(`${API_URL}/decisions/underwrite`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        application: appData,
        include_rag: false,
        force_model: forceModel,
      }),
    });
    if (!response.ok) throw new Error('Failed to make decision');
    return response.json();
  },

  async getDecision(decisionId: number) {
    const response = await fetch(`${API_URL}/decisions/${decisionId}`);
    if (!response.ok) throw new Error('Failed to get decision');
    return response.json();
  },

  async provideFeedback(decisionId: number, feedback: 'correct' | 'incorrect') {
    const response = await fetch(`${API_URL}/decisions/${decisionId}/feedback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ feedback }),
    });
    if (!response.ok) throw new Error('Failed to provide feedback');
    return response.json();
  },

  // Analytics
  async getRoutingAnalytics() {
    const response = await fetch(`${API_URL}/analytics/routing`);
    if (!response.ok) throw new Error('Failed to get routing analytics');
    return response.json();
  },

  async getBanditMetrics() {
    const response = await fetch(`${API_URL}/analytics/bandit`);
    if (!response.ok) throw new Error('Failed to get bandit metrics');
    return response.json();
  },

  async getSystemPerformance() {
    const response = await fetch(`${API_URL}/analytics/performance`);
    if (!response.ok) throw new Error('Failed to get system performance');
    return response.json();
  },

  async getModelComparison() {
    const response = await fetch(`${API_URL}/analytics/model-comparison`);
    if (!response.ok) throw new Error('Failed to get model comparison');
    return response.json();
  },
};
