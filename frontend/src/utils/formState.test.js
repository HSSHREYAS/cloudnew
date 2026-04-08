import { expect, test } from "vitest";
import { createInitialState, validatePayload } from "./formState.js";


test("creates service specific initial state", () => {
  const state = createInitialState("S3");

  expect(state.service).toBe("S3");
  expect(state.configuration.storage_class).toBe("Standard");
});


test("validates missing required values", () => {
  const errors = validatePayload({
    region: "",
    duration_hours: 0,
    configuration: {
      instance_type: "",
      operating_system: "Linux",
      pricing_model: "OnDemand",
    },
  });

  expect(errors.region).toBeTruthy();
  expect(errors.duration_hours).toBeTruthy();
  expect(errors.instance_type).toBeTruthy();
});
