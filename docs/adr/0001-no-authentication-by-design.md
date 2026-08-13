# No authentication by design

The assignment defines exactly two roles — a single predefined Owner and anonymous Guests — and explicitly rules out registration and login. All API operations, including Owner operations (creating Event Types, listing all Bookings), are therefore unauthenticated in the contract. This looks like a security hole but is a deliberate constraint of the task; do not "fix" it without revisiting the assignment.
