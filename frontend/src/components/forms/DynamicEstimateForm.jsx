import { useEffect, useState } from "react";

import { regionOptions, serviceCatalog } from "../../config/serviceCatalog.js";
import {
  createInitialState,
  normalizeFieldValue,
  validatePayload,
} from "../../utils/formState.js";
import ConfigurationFields from "./ConfigurationFields.jsx";

const serviceOptions = Object.keys(serviceCatalog);

export default function DynamicEstimateForm({ onSubmit, loading }) {
  const [service, setService] = useState("EC2");
  const [formState, setFormState] = useState(() => createInitialState("EC2"));
  const [errors, setErrors] = useState({});

  useEffect(() => {
    setFormState(createInitialState(service));
    setErrors({});
  }, [service]);

  const serviceMeta = serviceCatalog[service];

  function updateConfiguration(field, rawValue) {
    setFormState((current) => ({
      ...current,
      configuration: {
        ...current.configuration,
        [field.name]: normalizeFieldValue(field.type, rawValue),
      },
    }));
  }

  function handleSubmit(event) {
    event.preventDefault();
    const validationErrors = validatePayload(formState);
    setErrors(validationErrors);
    if (Object.keys(validationErrors).length > 0) {
      return;
    }
    onSubmit(formState);
  }

  return (
    <form className="panel form-panel" onSubmit={handleSubmit}>
      <div className="panel-header">
        <span className="eyebrow">Estimate</span>
        <h2>{serviceMeta.title}</h2>
        <p>{serviceMeta.summary}</p>
      </div>

      <label className="field">
        <span>Service</span>
        <select value={service} onChange={(event) => setService(event.target.value)}>
          {serviceOptions.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </label>

      <label className="field">
        <span>Region</span>
        <select
          value={formState.region}
          onChange={(event) =>
            setFormState((current) => ({ ...current, region: event.target.value }))
          }
        >
          {regionOptions.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
        {errors.region ? <small className="field-error">{errors.region}</small> : null}
      </label>

      <label className="field">
        <span>Duration (hours)</span>
        <input
          type="number"
          min="1"
          value={formState.duration_hours}
          onChange={(event) =>
            setFormState((current) => ({
              ...current,
              duration_hours: Number(event.target.value),
            }))
          }
        />
        {errors.duration_hours ? (
          <small className="field-error">{errors.duration_hours}</small>
        ) : null}
      </label>

      <div className="field-group">
        <div className="field-group-header">
          <h3>Service Inputs</h3>
          <span>Strictly validated by the backend</span>
        </div>
        <ConfigurationFields
          service={service}
          configuration={formState.configuration}
          errors={errors}
          onChange={updateConfiguration}
        />
      </div>

      <button type="submit" className="primary-button" disabled={loading}>
        {loading ? "Estimating..." : "Estimate Cost"}
      </button>
    </form>
  );
}
