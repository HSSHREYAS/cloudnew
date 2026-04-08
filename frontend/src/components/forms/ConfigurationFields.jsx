import { serviceCatalog } from "../../config/serviceCatalog.js";

export default function ConfigurationFields({ service, configuration, errors, onChange }) {
  return serviceCatalog[service].fields.map((field) => {
    const fieldValue = configuration[field.name] ?? "";
    return (
      <label className="field" key={field.name}>
        <span>{field.label}</span>
        {field.type === "select" ? (
          <select value={fieldValue} onChange={(event) => onChange(field, event.target.value)}>
            {field.options.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        ) : (
          <input
            type={field.type}
            min={field.min}
            placeholder={field.placeholder}
            value={fieldValue}
            onChange={(event) => onChange(field, event.target.value)}
          />
        )}
        {errors[field.name] ? <small className="field-error">{errors[field.name]}</small> : null}
      </label>
    );
  });
}
