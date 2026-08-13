# Fixed Business Hours instead of owner-configurable availability

Slots are generated inside a fixed daily interval — 09:00–18:00 in the Owner's timezone — hardcoded as a system constant. We considered giving the Owner a configurable availability schedule (the Cal.com model), but the assignment defines no such Owner scenario, so that flexibility was rejected to keep scope minimal. If availability configuration is ever introduced, it replaces the Business Hours constant and changes slot generation.
