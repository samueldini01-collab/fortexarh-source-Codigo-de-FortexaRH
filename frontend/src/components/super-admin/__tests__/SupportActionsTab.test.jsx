import { render, screen, fireEvent } from "@testing-library/react";
import SupportActionsTab from "../SupportActionsTab";

describe("SupportActionsTab", () => {
  it("renders the empty state when there are no actions", () => {
    render(<SupportActionsTab actions={[]} loading={false} onRefresh={jest.fn()} />);
    expect(screen.getByTestId("no-support-actions")).toBeInTheDocument();
    expect(screen.getByText(/Sin acciones registradas/)).toBeInTheDocument();
  });

  it("renders the section header and the refresh button", () => {
    render(<SupportActionsTab actions={[]} loading={false} onRefresh={jest.fn()} />);
    expect(screen.getByText("Acciones de soporte")).toBeInTheDocument();
    expect(screen.getByTestId("support-actions-refresh-btn")).toBeInTheDocument();
  });

  it("calls onRefresh when the refresh button is clicked", () => {
    const onRefresh = jest.fn();
    render(<SupportActionsTab actions={[]} loading={false} onRefresh={onRefresh} />);
    fireEvent.click(screen.getByTestId("support-actions-refresh-btn"));
    expect(onRefresh).toHaveBeenCalledTimes(1);
  });

  it("disables the refresh button while loading", () => {
    render(<SupportActionsTab actions={[]} loading={true} onRefresh={jest.fn()} />);
    const btn = screen.getByTestId("support-actions-refresh-btn");
    expect(btn).toBeDisabled();
  });

  it("renders one row per action with the data-testid based on id", () => {
    const actions = [
      { id: "a-1", created_at: "2026-03-15T10:30:00Z", email: "support@x.com", method: "POST",   path: "/api/employees",  query: "",   status_code: 201, ip: "1.1.1.1" },
      { id: "a-2", created_at: "2026-03-15T10:31:00Z", email: "support@x.com", method: "DELETE", path: "/api/employees/123", query: "", status_code: 204, ip: "1.1.1.1" },
    ];
    render(<SupportActionsTab actions={actions} loading={false} onRefresh={jest.fn()} />);
    expect(screen.getByTestId("support-action-a-1")).toBeInTheDocument();
    expect(screen.getByTestId("support-action-a-2")).toBeInTheDocument();
  });

  it("renders the method badges (POST/DELETE/PATCH)", () => {
    const actions = [
      { id: "p", created_at: "2026-03-01T00:00:00Z", email: "x", method: "POST",   path: "/api/x", status_code: 200, ip: "" },
      { id: "d", created_at: "2026-03-01T00:00:00Z", email: "x", method: "DELETE", path: "/api/x", status_code: 204, ip: "" },
      { id: "u", created_at: "2026-03-01T00:00:00Z", email: "x", method: "PATCH",  path: "/api/x", status_code: 200, ip: "" },
    ];
    render(<SupportActionsTab actions={actions} loading={false} onRefresh={jest.fn()} />);
    expect(screen.getByText("POST")).toBeInTheDocument();
    expect(screen.getByText("DELETE")).toBeInTheDocument();
    expect(screen.getByText("PATCH")).toBeInTheDocument();
  });

  it("appends ?query to the endpoint path when query is non-empty", () => {
    const actions = [
      { id: "q", created_at: "2026-03-01T00:00:00Z", email: "x", method: "GET", path: "/api/r", query: "search=acme", status_code: 200, ip: "" },
    ];
    render(<SupportActionsTab actions={actions} loading={false} onRefresh={jest.fn()} />);
    expect(screen.getByText("/api/r?search=acme")).toBeInTheDocument();
  });

  it("renders an em dash when ip is empty", () => {
    const actions = [
      { id: "i", created_at: "2026-03-01T00:00:00Z", email: "x", method: "GET", path: "/api/r", query: "", status_code: 200, ip: "" },
    ];
    render(<SupportActionsTab actions={actions} loading={false} onRefresh={jest.fn()} />);
    expect(screen.getByText("—")).toBeInTheDocument();
  });

  it("renders the status code with the row data", () => {
    const actions = [
      { id: "s", created_at: "2026-03-01T00:00:00Z", email: "x", method: "POST", path: "/api/r", query: "", status_code: 201, ip: "" },
    ];
    render(<SupportActionsTab actions={actions} loading={false} onRefresh={jest.fn()} />);
    expect(screen.getByText("201")).toBeInTheDocument();
  });
});
