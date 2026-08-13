# End-to-end scenarios

The e2e suite drives the fully assembled system — a real browser against the real
backend — through the journeys of the two roles in the domain: the Guest and the
Owner. Every scenario is written in the domain language (Guest, Owner, Event
Type, Slot, Booking, Owner Area) and asserted on external behavior only: what the
Guest or the Owner sees on screen and what the public API returns.

The four scenarios are numbered S1–S4. Tests reference these numbers in their
names.

## S1 — Guest books a Slot

Preconditions: a dedicated Event Type for this scenario is offered in the
catalog.

1. The Guest opens the catalog and sees the Event Type.
2. The Guest opens the Event Type and sees its free Slots; the Guest picks the
   first free Slot.
3. The Guest fills in the booking form — name, email and an optional comment —
   and submits.
4. The Guest lands on the confirmation screen, and the Booking is confirmed.

## S2 — a booked Slot is no longer offered

Preconditions: a dedicated Event Type for this scenario is offered in the
catalog, and a Booking on one of its Slots was just created.

1. The Guest opens the Event Type and sees the free Slots.
2. The Guest books the first free Slot (as in S1).
3. The Guest re-opens the Event Type's Slots.
4. The booked Slot is no longer offered.

## S3 — a Booking appears in the Owner Area

Preconditions: a dedicated Event Type for this scenario is offered in the
catalog, and a Booking on one of its Slots was just created.

1. The Guest books the first free Slot (as in S1).
2. The Owner opens the Owner Area and sees the upcoming Bookings.
3. The Booking created in step 1 is shown, with its Slot and Guest details.

## S4 — the Owner creates an Event Type through the Owner Area

Preconditions: the Owner Area is open.

1. The Owner opens the Owner Area and creates a new Event Type — slug, name,
   description and duration — through the Owner Area UI.
2. The Owner is returned to the catalog.
3. The Guest catalog offers the new Event Type.
