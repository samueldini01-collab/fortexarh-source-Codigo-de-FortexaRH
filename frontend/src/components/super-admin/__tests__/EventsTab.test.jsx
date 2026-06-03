import { render, screen } from "@testing-library/react";
import EventsTab from "../EventsTab";

describe("EventsTab", () => {
  it("renders the empty state when there are no events", () => {
    render(<EventsTab events={[]} />);
    expect(screen.getByText(/No hay eventos registrados/)).toBeInTheDocument();
  });

  it("renders the section title", () => {
    render(<EventsTab events={[]} />);
    expect(screen.getByText("Eventos del Sistema")).toBeInTheDocument();
  });

  it("renders one row per event with event_type and company badge", () => {
    const events = [
      {
        event_id: "evt-1",
        event_type: "user_login",
        company_name: "Acme S.A.",
        description: "Admin logged in",
        created_at: "2026-03-15T10:30:00Z",
        user_email: "admin@acme.com",
      },
      {
        event_id: "evt-2",
        action: "payroll_approved",
        company_name: "Beta Co",
        details: "Payroll Q1 March approved",
        timestamp: "2026-03-12T09:00:00Z",
        user_email: "rh@beta.com",
      },
    ];
    render(<EventsTab events={events} />);
    expect(screen.getByText("user_login")).toBeInTheDocument();
    expect(screen.getByText("payroll_approved")).toBeInTheDocument();
    expect(screen.getByText("Acme S.A.")).toBeInTheDocument();
    expect(screen.getByText("Beta Co")).toBeInTheDocument();
    expect(screen.getByText("Admin logged in")).toBeInTheDocument();
    expect(screen.getByText("Payroll Q1 March approved")).toBeInTheDocument();
  });

  it("renders 'evento' as fallback when event_type and action are missing", () => {
    render(<EventsTab events={[{ event_id: "e", description: "x", created_at: "2026-01-01T00:00:00Z" }]} />);
    expect(screen.getByText("evento")).toBeInTheDocument();
  });

  it("formats the timestamp (replaces T with space and truncates to 19 chars)", () => {
    render(
      <EventsTab events={[{ event_id: "e", event_type: "x", created_at: "2026-03-15T10:30:45.123Z", user_email: "a@b.com" }]} />,
    );
    expect(screen.getByText(/2026-03-15 10:30:45/)).toBeInTheDocument();
    expect(screen.getByText(/a@b\.com/)).toBeInTheDocument();
  });

  it("omits the company badge when company_name is missing", () => {
    const events = [{ event_id: "e1", event_type: "system", description: "Sin empresa", created_at: "2026-01-01T00:00:00Z" }];
    render(<EventsTab events={events} />);
    expect(screen.getByText("system")).toBeInTheDocument();
    expect(screen.queryByText("Acme S.A.")).not.toBeInTheDocument();
  });
});
