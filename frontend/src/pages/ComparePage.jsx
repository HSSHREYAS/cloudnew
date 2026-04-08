import { useState } from "react";

import ComparisonChart from "../components/charts/ComparisonChart.jsx";
import CompareForm from "../components/forms/CompareForm.jsx";
import { useAuth } from "../auth/AuthContext.jsx";
import { compareConfigurations } from "../services/costAdvisorApi.js";

export default function ComparePage() {
  const { getToken } = useAuth();
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [bestOption, setBestOption] = useState(null);
  const [error, setError] = useState("");

  async function handleCompare(payload) {
    setLoading(true);
    setError("");

    try {
      const comparison = await compareConfigurations(getToken, payload);
      setResults(comparison.results);
      setBestOption(comparison.best_option);
    } catch (requestError) {
      setError(requestError.response?.data?.error?.message || "Unable to compare configurations right now.");
      setResults([]);
      setBestOption(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page-grid compare-page">
      <CompareForm onSubmit={handleCompare} loading={loading} />

      <section className="panel results-panel">
        <div className="panel-header">
          <span className="eyebrow">Comparison</span>
          <h2>Cross-Region Cost Analysis</h2>
          <p>Rank deployment options by projected total cost using the shared estimation engine.</p>
        </div>

        {error ? <div className="error-banner">{error}</div> : null}

        <ComparisonChart data={results} />

        <section className="sub-panel">
          <h3>Best Option</h3>
          <p>
            {bestOption
              ? `${bestOption.region} is the lowest-cost option at $${bestOption.total_cost.toFixed(4)}.`
              : "Run a comparison to identify the lowest-cost option."}
          </p>
        </section>

        <section className="sub-panel">
          <h3>Ranked Results</h3>
          <ul className="metric-list">
            {results.map((result) => (
              <li key={`${result.region}-${result.total_cost}`}>
                <strong>{result.region}</strong>
                <span>{result.service}</span>
                <span>${result.total_cost.toFixed(4)}</span>
              </li>
            ))}
          </ul>
        </section>
      </section>
    </div>
  );
}
