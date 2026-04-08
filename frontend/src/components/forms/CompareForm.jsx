import { useEffect, useState } from "react";

import { regionOptions, serviceCatalog } from "../../config/serviceCatalog.js";
import {
  createInitialState,
  normalizeFieldValue,
  validatePayload,
} from "../../utils/formState.js";
import ConfigurationFields from "./ConfigurationFields.jsx";

export default function CompareForm({ onSubmit, loading }) {
  const [service, setService] = useState("EC2");
  const [durationHours, setDurationHours] = useState(100);
  const [comparisons, setComparisons] = useState([
    createInitialState("EC2"),
    { ...createInitialState("EC2"), region: "us-west-2" },
  ]);
  const [errors, setErrors] = useState({});

  useEffect(() => {
    setComparisons([
      createInitialState(service),
      {
        ...createInitialState(service),
        region: serviceCatalog[service].defaultValues.region === "us-east-1" ? "us-west-2" : "us-east-1",
      },
    ]);
    setDurationHours(serviceCatalog[service].defaultValues.duration_hours);
    setErrors({});
  }, [service]);

  function updateComparison(index, updater) {
    setComparisons((current) => current.map((item, itemIndex) => (itemIndex === index ? updater(item) : item)));
  }

  function handleSubmit(event) {
    event.preventDefault();
    const nextErrors = comparisons.map((item) => validatePayload(item, { requireDuration: false }));
    setErrors(nextErrors);
    if (nextErrors.some((entry) => Object.keys(entry).length > 0)) {
      return;
    }

    onSubmit({
      service,
      duration_hours: durationHours,
      comparisons: comparisons.map((item) => ({
        region: item.region,
        configuration: item.configuration,
      })),
    });
  }

  return (
    <form className="panel form-panel" onSubmit={handleSubmit}>
      <div className="panel-header">
        <span className="eyebrow">Compare</span>
        <h2>Region and Configuration Comparison</h2>
        <p>Evaluate at least two deployment candidates with the same service-aware schema.</p>
      </div>

      <label className="field">
        <span>Service</span>
        <select value={service} onChange={(event) => setService(event.target.value)}>
          {Object.keys(serviceCatalog).map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </label>

      <label className="field">
        <span>Duration (hours)</span>
        <input
          type="number"
          min="1"
          value={durationHours}
          onChange={(event) => setDurationHours(Number(event.target.value))}
        />
      </label>

      <div className="compare-grid">
        {comparisons.map((comparison, index) => (
          <section className="compare-card" key={`${service}-${index}`}>
            <div className="field-group-header">
              <h3>Candidate {index + 1}</h3>
              <span>{serviceCatalog[service].title}</span>
            </div>

            <label className="field">
              <span>Region</span>
              <select
                value={comparison.region}
                onChange={(event) =>
                  updateComparison(index, (current) => ({
                    ...current,
                    region: event.target.value,
                  }))
                }
              >
                {regionOptions.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </label>

            <ConfigurationFields
              service={service}
              configuration={comparison.configuration}
              errors={errors[index] || {}}
              onChange={(field, value) =>
                updateComparison(index, (current) => ({
                  ...current,
                  configuration: {
                    ...current.configuration,
                    [field.name]: normalizeFieldValue(field.type, value),
                  },
                }))
              }
            />
          </section>
        ))}
      </div>

      <button type="submit" className="primary-button" disabled={loading}>
        {loading ? "Comparing..." : "Compare Options"}
      </button>
    </form>
  );
}
