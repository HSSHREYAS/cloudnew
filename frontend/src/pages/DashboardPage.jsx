import { useState } from "react";

import CostBreakdownChart from "../components/charts/CostBreakdownChart.jsx";
import DynamicEstimateForm from "../components/forms/DynamicEstimateForm.jsx";
import { useAuth } from "../auth/AuthContext.jsx";
import { estimateCost, fetchRecommendations } from "../services/costAdvisorApi.js";

export default function DashboardPage() {
  const { getToken } = useAuth();
  const [loading, setLoading] = useState(false);
  const [estimate, setEstimate] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [error, setError] = useState("");

  async function handleEstimate(payload) {
    setLoading(true);
    setError("");

    try {
      const estimateData = await estimateCost(getToken, payload);
      setEstimate(estimateData);

      const recommendationData = await fetchRecommendations(getToken, {
        service: payload.service,
        region: payload.region,
        duration_hours: payload.duration_hours,
        current_cost: estimateData.total_cost,
        configuration: payload.configuration,
      });
      setRecommendations(recommendationData.recommendations);
    } catch (requestError) {
      setError(requestError.response?.data?.error?.message || "Unable to estimate cost right now.");
      setEstimate(null);
      setRecommendations([]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page-grid">
      <DynamicEstimateForm onSubmit={handleEstimate} loading={loading} />

      <section className="panel results-panel">
        <div className="panel-header">
          <span className="eyebrow">Dashboard</span>
          <h2>Cost Breakdown & Why This Configuration</h2>
          <p>Each estimate shows the pricing source, assumptions, and optimization opportunities.</p>
        </div>

        {error ? <div className="error-banner">{error}</div> : null}

        <div className="stats-grid">
          <article className="stat-card">
            <span>Total Cost</span>
            <strong>{estimate ? `$${estimate.total_cost.toFixed(4)}` : "--"}</strong>
          </article>
          <article className="stat-card">
            <span>Currency</span>
            <strong>{estimate?.currency || "--"}</strong>
          </article>
          <article className="stat-card">
            <span>Recommendations</span>
            <strong>{recommendations.length}</strong>
          </article>
        </div>

        <CostBreakdownChart data={estimate?.breakdown || []} />

        <div className="insights-grid">
          <section className="sub-panel">
            <h3>Line Items</h3>
            <ul className="metric-list">
              {(estimate?.breakdown || []).map((item) => (
                <li key={item.label}>
                  <strong>{item.label}</strong>
                  <span>{item.description}</span>
                  <span>${item.amount.toFixed(4)}</span>
                </li>
              ))}
            </ul>
          </section>

          <section className="sub-panel">
            <h3>Recommendation Engine</h3>
            <ul className="recommendation-list">
              {recommendations.map((item) => (
                <li key={`${item.suggestion}-${item.type}`}>
                  <strong>{item.suggestion}</strong>
                  <span>{item.explanation}</span>
                  <span>Estimated savings: ${item.estimated_savings.toFixed(4)}</span>
                </li>
              ))}
            </ul>
          </section>
        </div>

        <section className="sub-panel">
          <h3>Why This Configuration?</h3>
          <pre className="metadata-block">
            {estimate ? JSON.stringify(estimate.metadata, null, 2) : "Estimate metadata will appear here."}
          </pre>
        </section>
      </section>
    </div>
  );
}
