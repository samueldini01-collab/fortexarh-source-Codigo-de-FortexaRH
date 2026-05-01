# FortexaRH — Test Credentials

## Super Admin
- Email/Username: `fortexa2026rd`
- Password: `FortexaAdmin2026!`
- Login endpoint may require an alternative form (not standard email validator). Use the dedicated super-admin login flow if available.

## Admin User (regular company tenant)
- Email: `test_refactor@fortexa.com`
- Password: `test123`
- Role: admin
- Company country: DO (República Dominicana) — relevant for native-format country guards.

## Employee Portal
- Cédula / ID: `001-0000001-1`
- Password: `portal123`

## Notes for Testing Agent
- Native reports require the company's `country` to match the format's expected country (returns HTTP 400 with a guidance message if not).
- The test admin company (`test_refactor@fortexa.com`) is configured as DO, so calling endpoints like `/api/native-reports/cl/previred` will return a 400 guard — this is the expected behavior, not a bug.
- To validate format generation end-to-end, change the company country from Settings to the relevant country (CL, PE, EC, etc.) before calling the corresponding endpoint, OR seed a separate company with the target country.
- APScheduler runs `run_reminders_for_all_companies` daily at 08:00 UTC. The `/api/native-reports/calendar/run-reminders-all` endpoint can be used to trigger it manually (admin/super_admin only).
