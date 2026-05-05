import React, { useState } from 'react';
import { apiService, Application } from '../services/api';
import '../styles/ApplicationForm.css';

const EMPLOYMENT_OPTIONS = [
  'employed',
  'self-employed',
  'retired',
  'unemployed',
  'student',
];

const LOAN_PURPOSES = [
  'personal',
  'home',
  'auto',
  'business',
  'debt_consolidation',
  'education',
];

export default function ApplicationForm() {
  const [formData, setFormData] = useState<Application>({
    full_name: '',
    email: '',
    phone: '',
    date_of_birth: '',
    gender: '',
    street_address: '',
    city: '',
    state: '',
    postal_code: '',
    country: '',
    annual_income: 0,
    monthly_expenses: 0,
    employment_status: 'employed',
    years_employed: 0,
    employer: '',
    credit_score: 650,
    existing_debts: 0,
    number_of_accounts: 0,
    delinquencies: 0,
    loan_amount: 0,
    loan_term_months: 60,
    loan_purpose: 'personal',
    collateral_value: undefined,
    applicant_notes: '',
  });

  const [decision, setDecision] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'number' ? parseFloat(value) || 0 : value,
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError(null);
      const result = await apiService.underwrite(formData);
      setDecision(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to process application');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="application-form-container">
      <h2>New Application</h2>

      {decision && (
        <div className="decision-result">
          <div className={`decision-card ${decision.decision}`}>
            <h3>Decision: {decision.decision.toUpperCase()}</h3>
            <p className="confidence">Confidence: {(decision.confidence * 100).toFixed(1)}%</p>
            <p className="risk">Risk Score: {(decision.risk_score * 100).toFixed(1)}%</p>

            {decision.approved_amount && (
              <p className="approved-amount">Approved Amount: ${decision.approved_amount.toFixed(2)}</p>
            )}

            {decision.offered_interest_rate && (
              <p className="interest-rate">Interest Rate: {(decision.offered_interest_rate * 100).toFixed(2)}%</p>
            )}

            <div className="explanation">
              <h4>Explanation:</h4>
              <p>{decision.explanation}</p>
            </div>

            <div className="metrics">
              <p>Model Used: <strong>{decision.model_used}</strong></p>
              <p>Latency: <strong>{decision.latency_ms.toFixed(0)}ms</strong></p>
              <p>Tokens Used: <strong>{decision.total_tokens_used}</strong></p>
              <p>Estimated Cost: <strong>${decision.estimated_cost.toFixed(4)}</strong></p>
            </div>

            <button onClick={() => setDecision(null)}>Process Another Application</button>
          </div>
        </div>
      )}

      {!decision && (
        <form onSubmit={handleSubmit} className="application-form">
          {error && <div className="error-message">{error}</div>}

          <fieldset>
            <legend>Personal Information</legend>
            <input
              type="text"
              name="full_name"
              placeholder="Full Name"
              value={formData.full_name}
              onChange={handleInputChange}
              required
            />
            <input
              type="email"
              name="email"
              placeholder="Email"
              value={formData.email}
              onChange={handleInputChange}
              required
            />
            <input
              type="tel"
              name="phone"
              placeholder="Phone"
              value={formData.phone}
              onChange={handleInputChange}
              required
            />
            <input
              type="date"
              name="date_of_birth"
              value={formData.date_of_birth}
              onChange={handleInputChange}
              required
            />
            <select
              name="gender"
              value={formData.gender}
              onChange={handleInputChange}
              required
            >
              <option value="">Select Gender</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="other">Other</option>
            </select>
          </fieldset>

          <fieldset>
            <legend>Address Information</legend>
            <input
              type="text"
              name="street_address"
              placeholder="Street Address"
              value={formData.street_address}
              onChange={handleInputChange}
              required
            />
            <input
              type="text"
              name="city"
              placeholder="City"
              value={formData.city}
              onChange={handleInputChange}
              required
            />
            <input
              type="text"
              name="state"
              placeholder="State"
              value={formData.state}
              onChange={handleInputChange}
              required
            />
            <input
              type="text"
              name="postal_code"
              placeholder="Postal Code"
              value={formData.postal_code}
              onChange={handleInputChange}
              required
            />
            <input
              type="text"
              name="country"
              placeholder="Country"
              value={formData.country}
              onChange={handleInputChange}
              required
            />
          </fieldset>

          <fieldset>
            <legend>Financial Information</legend>
            <input
              type="number"
              name="annual_income"
              placeholder="Annual Income"
              value={formData.annual_income}
              onChange={handleInputChange}
              required
            />
            <input
              type="number"
              name="monthly_expenses"
              placeholder="Monthly Expenses"
              value={formData.monthly_expenses}
              onChange={handleInputChange}
              required
            />
            <select
              name="employment_status"
              value={formData.employment_status}
              onChange={handleInputChange}
              required
            >
              <option value="">Select Employment Status</option>
              {EMPLOYMENT_OPTIONS.map(opt => (
                <option key={opt} value={opt}>{opt}</option>
              ))}
            </select>
            <input
              type="number"
              name="years_employed"
              placeholder="Years Employed"
              value={formData.years_employed}
              onChange={handleInputChange}
              step="0.5"
              required
            />
            <input
              type="text"
              name="employer"
              placeholder="Employer"
              value={formData.employer}
              onChange={handleInputChange}
              required
            />
          </fieldset>

          <fieldset>
            <legend>Credit Information</legend>
            <input
              type="number"
              name="credit_score"
              placeholder="Credit Score (300-850)"
              value={formData.credit_score}
              onChange={handleInputChange}
              min="300"
              max="850"
              required
            />
            <input
              type="number"
              name="existing_debts"
              placeholder="Existing Debts"
              value={formData.existing_debts}
              onChange={handleInputChange}
              required
            />
            <input
              type="number"
              name="number_of_accounts"
              placeholder="Number of Active Accounts"
              value={formData.number_of_accounts}
              onChange={handleInputChange}
              required
            />
            <input
              type="number"
              name="delinquencies"
              placeholder="Number of Delinquencies"
              value={formData.delinquencies}
              onChange={handleInputChange}
              min="0"
              required
            />
          </fieldset>

          <fieldset>
            <legend>Loan Request</legend>
            <input
              type="number"
              name="loan_amount"
              placeholder="Loan Amount"
              value={formData.loan_amount}
              onChange={handleInputChange}
              required
            />
            <input
              type="number"
              name="loan_term_months"
              placeholder="Loan Term (months)"
              value={formData.loan_term_months}
              onChange={handleInputChange}
              required
            />
            <select
              name="loan_purpose"
              value={formData.loan_purpose}
              onChange={handleInputChange}
              required
            >
              <option value="">Select Loan Purpose</option>
              {LOAN_PURPOSES.map(purpose => (
                <option key={purpose} value={purpose}>{purpose}</option>
              ))}
            </select>
            <input
              type="number"
              name="collateral_value"
              placeholder="Collateral Value (optional)"
              value={formData.collateral_value || ''}
              onChange={handleInputChange}
            />
          </fieldset>

          <fieldset>
            <legend>Additional Information</legend>
            <textarea
              name="applicant_notes"
              placeholder="Additional Notes"
              value={formData.applicant_notes}
              onChange={handleInputChange}
              rows={4}
            />
          </fieldset>

          <button type="submit" disabled={loading} className="submit-button">
            {loading ? 'Processing...' : 'Submit Application'}
          </button>
        </form>
      )}
    </div>
  );
}
