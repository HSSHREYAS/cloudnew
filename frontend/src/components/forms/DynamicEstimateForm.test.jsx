import { expect, test } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import DynamicEstimateForm from "./DynamicEstimateForm.jsx";


test("switches fields when service changes", async () => {
  const user = userEvent.setup();
  render(<DynamicEstimateForm loading={false} onSubmit={() => {}} />);

  expect(screen.getByLabelText(/Instance Type/i)).toBeInTheDocument();

  await user.selectOptions(screen.getByLabelText(/Service/i), "Lambda");

  expect(screen.getByLabelText(/Request Count/i)).toBeInTheDocument();
  expect(screen.queryByLabelText(/Instance Type/i)).not.toBeInTheDocument();
});
