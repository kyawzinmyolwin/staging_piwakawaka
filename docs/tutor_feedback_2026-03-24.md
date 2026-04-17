# Tutor Feedback Summary — 2026-03-24

## General UI

- "Welcome back" row on dashboards needs restyling
- Success toast in bottom-right is too subtle — make it more noticeable
- Some pages are missing a back button to the parent page (e.g. Add Trap)
- Long list pages need pagination

---

## US10 — View Lines & Traps

- The "Active / Inactive" status column is confusing — needs to be clearer
- "Add Trap" and "Add Catch Record" buttons should be at the top of the page
- After adding a trap, show a flash success message that disappears on next load

---

## US12 — Line Assignments (Zhenghang)

- Assignment page is missing / broken
- Inactive lines should not appear in the assignment page
- The dropdown should not include the operator who is already assigned to the line
- Assignment dates all look the same — needs to clearly show who is **currently** assigned vs historical records

---

## US13 — Add Catch Record (Operator)

- Operators should only see lines assigned to them
- Lines not assigned to the operator should not show an "Add Catch Record" button
- Operators should not be able to add a catch to a trap that isn't on their assigned line
- If a trap already has a catch record with a non-None species, strikes should not default to 0

---

## US15 — Browse & Filter Catch Data (Yu)

- Time format is wrong in UAT — check NZ timezone display
- Catch list needs pagination when there are many records

### Additional issues based on tutor's feedback pattern

1. **Should operators only see catches from their assigned lines?** The tutor's thinking is role-based — the catch list may need a default filter for operators showing only their lines, or at least a "My lines only" toggle
2. **Is "Recorded by" visible in the catch list?** The tutor kept asking who is currently doing what — this field should be clearly shown
3. **Records with strikes = 0 but species ≠ None** — consider flagging or filtering these as they are visually misleading
4. **Date format consistency** — tutor specifically mentioned time format; make sure all dates in the catch list display in NZ time and follow a consistent format (`DD/MM/YYYY HH:MM` or similar)
5. **CSV download (US17)** — the download button belongs on the catch list page, which is your page
