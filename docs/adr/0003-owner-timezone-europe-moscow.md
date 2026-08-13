# Owner timezone fixed as Europe/Moscow

The contract defines days, the Booking Window and slot grids "in the Owner's fixed timezone" but never names that timezone, and the API does not expose it. We fix the Owner's timezone as Europe/Moscow: a system constant that the frontend (and the future backend) must share out of band. The UI renders all Slot and Booking times in this timezone, labelled, rather than in the visitor's browser timezone, so that day boundaries match the server's Booking Window exactly.

## Consequences

- Both frontend and backend hardcode the same constant; changing it requires a coordinated change on both sides.
- Guests in other timezones see Owner-local wall-clock times; the UI labels the timezone (e.g. «МСК») to prevent ambiguity.
