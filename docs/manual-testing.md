# Manual Testing Scenarios

This guide provides end-to-end manual test flows for the Coffee Fund App focusing on the per‑user PIN model, self-service top-ups, and two-person confirmation rule.

## Conventions
- "PIN" always refers to an individual user's 4+ digit secret (hashed server-side)
- All IDs are UUID; you normally interact via UI, not raw IDs
- Amount examples use a decimal (e.g. 12.50) which is converted to integer cents in backend

---
## 1. Environment Bootstrap
1. `make dev` to start services (Postgres, backend, frontend)
2. Navigate to http://localhost:3000
3. Ensure at least one Admin/Treasurer account exists (seed or create). Create additional users as needed.
4. Verify language default (German) and that toggle works switching to English and back.

Expected: No console errors, UI loads product list (if seeded) and user selection components.

---
## 2. User PIN Access Flow
1. On Dashboard, select a regular user (non-treasurer)
2. Enter correct user PIN when prompted
3. Observe user-specific dashboard content (balance, top consumers, etc.)

Negative Cases:
- Enter wrong PIN → Expect inline error / toast; user context should not unlock
- Multiple wrong attempts (manual) → Still blocked (future enhancement: rate limiting)

---
## 3. Self-Service Top-Up Request
1. While viewing a user context (after PIN success), click "Top Up Balance"
2. In modal:
   - Amount: 12.50
   - Note: "Refill"
   - Re-enter user PIN (second confirmation)
3. Submit

Expected:
- Success toast (e.g. creation/pending message)
- Pending money move visible in Pending list (status: pending, type: deposit, amount_cents=1250)
- Balance NOT yet updated (still old balance)

Negative Cases:
- Leave amount empty or 0 → validation blocks submit
- Enter malformed (letters) → sanitized or rejected with error
- Wrong PIN in modal → error toast, move NOT created

---
## 4. Treasurer Confirmation (Two-Person Rule)
1. Switch to (select) Treasurer A who originally DID NOT create the pending move (or ensure the pending move was created by a regular user)
2. Enter Treasurer A PIN
3. Navigate to Treasurer / Pending Confirmations section
4. Locate the pending deposit → Confirm
5. Enter Treasurer A PIN in confirmation (if prompted)

Expected:
- If Treasurer A is same as creator (should be prevented) → backend rejection
- Using a different treasurer (Treasurer B if creator was Treasurer A) → confirmation succeeds
- Balance now increases by 12.50 for user
- Pending item disappears from pending list

---
## 5. Product Consumption Booking
1. Kiosk page → Select same user → Enter PIN
2. Click a product (e.g. Coffee) once: confirm booking dialog (if implemented) OR immediate booking
3. Verify new consumption appears in history and balance decreases by product price

Edge Cases:
- Rapid double clicks → Should not create duplicate if backend idempotency or UI disable is correct
- Inactive product should not be selectable

---
## 6. PIN Change (User Self-Service)
1. In user dashboard, initiate Change PIN (if implemented)
2. Provide current PIN + new PIN
3. Submit
4. Log out (deselect) by selecting another user, then re-select original user
5. Enter OLD PIN → should fail
6. Enter NEW PIN → should succeed

---
## 7. Admin PIN Reset
1. As Admin/Treasurer with admin rights, open Users page
2. Choose a user → Reset PIN to default (1234)
3. Re-select user and login with 1234
4. Prompt user to change default PIN (best practice – if UI not enforcing yet, note as enhancement)

---
## 8. Internationalization Regression
1. Switch language to English
2. Open Top-Up modal → labels for Amount, Note, PIN, confirmation message present
3. Switch to German → same fields localized
4. Ensure no `[missing]` or console i18n warnings

---
## 9. Audit Trail Spot Check
1. Perform: user top-up request + treasurer confirmation + product consumption
2. (Backend) Query audit endpoint (or DB if direct access) to ensure 3+ entries:
   - money_move.create (pending)
   - money_move.confirm (confirmed)
   - consumption.create

Fields should include actor_id and entity metadata.

---
## 10. Deactivation / Deletion Safeguards
1. Attempt to delete last remaining admin → should fail (or be blocked in UI)
2. Deactivate a regular user → user should no longer appear in active selection lists
3. Reactivate user → selection restored

---
## 11. Error & Edge Handling
| Scenario | Expected Behavior |
|----------|-------------------|
| Network 500 on top-up submit | Toast error; no duplicate pending move |
| PIN field empty submit | Inline validation error; no request sent |
| Amount extremely large (e.g. 999999) | Either accepted (if within int bounds) or validated per business rule |
| Floating precision (e.g. 0.015) | Rounded to nearest cent (verify) |
| Concurrent confirmation (two treasurers) | Only first succeeds; second gets conflict / already confirmed state |

---
## 12. Cleanup
- Optionally purge test users/products via Admin/Treasurer UI
- Confirm no orphan pending moves

---
## Pending Enhancements (Not Yet Implemented)
- Rate limiting on wrong PIN attempts
- Email notifications for large deposits
- Per-action mandatory PIN re-prompt for all treasurer-sensitive actions
- Timezone-aware timestamps (UTC enforcement)

---
## Quick Reference
- Top-Up Modal test ids: `topup-amount`, `topup-pin`, `topup-note`, `topup-submit`
- i18n new keys: see README "Added i18n Keys (Recent)"
- Two-person rule: creator != confirmer (both must be treasurers OR creator may be regular user for self-service; confirmer must be treasurer)

Happy testing! :coffee:
