# Manual Testing Guide: User-Initiated Money Moves (Dashboard PIN Flow)

## Prerequisites
1. Development environment running (`make dev`)
2. Database migrated (`make migrate`) 
3. At least one admin, one treasurer, and one regular user created
4. Application philosophy: No persistent login session – per-user access is gated by on-demand PIN verification on the Dashboard. Users re‑enter PIN for sensitive actions (top-up).

## Test Scenarios

### Scenario 1: Basic User Money Move Creation (Dashboard)

**Objective**: Verify a user can self‑initiate a deposit request from the Dashboard using only PIN confirmation (no login session).

**Steps**:
1. Go to Dashboard
2. Select the user in the user picker (do not log in – just select)
3. Inline PIN panel appears; enter correct PIN and confirm access
4. Balance + actions area appears for that user
5. Click "Top Up Balance"
6. In modal enter:
  - Amount: €10.00
  - Note: `Test self deposit`
  - Re-enter PIN (modal requires a fresh PIN entry)
7. Submit
8. Observe success toast
9. Modal closes; pending move appears under "Pending Confirmations" (status pending)

**Expected Results**:
- ✅ Inline PIN gating required before any user-sensitive data appears
- ✅ Top Up button visible after successful PIN verification
- ✅ Modal enforces second PIN entry (re-auth for action)
- ✅ Request created with status "pending"
- ✅ Balance not yet updated until confirmation

### Scenario 2: Treasurer Confirmation of User Request

**Objective**: Verify treasurers can confirm user-initiated requests

**Steps**:
1. Switch to treasurer account
2. Navigate to Treasurer page
3. Locate the pending money move created in Scenario 1
4. Verify it shows:
   - Created by: Regular user
   - Status: Pending
   - Amount: €10.00
5. Click "Confirm" button
6. Enter treasurer PIN
7. Verify confirmation succeeds
8. Check that status changes to "Confirmed"

**Expected Results**:
- ✅ Pending request visible to treasurer
- ✅ Correct creator attribution
- ✅ Confirmation requires treasurer PIN
- ✅ Status updates to confirmed
- ✅ User's balance increases

### Scenario 3: Security Constraints

**Objective**: Verify security measures work correctly

**Steps**:
1. Try to access the new API endpoint directly:
   ```bash
   curl -X POST http://localhost:8000/money-moves/user-request \
     -H "Content-Type: application/json" \
     -H "x-actor-id: USER_ID_1" \
     -H "x-actor-pin: CORRECT_PIN" \
     -d '{
       "type": "deposit",
       "user_id": "USER_ID_2",
       "amount_cents": 1000,
       "note": "Trying to create for another user"
     }'
   ```

2. Try with incorrect PIN:
   ```bash
   curl -X POST http://localhost:8000/money-moves/user-request \
     -H "Content-Type: application/json" \
     -H "x-actor-id: USER_ID" \
     -H "x-actor-pin: WRONG_PIN" \
     -d '{
       "type": "deposit",
       "user_id": "USER_ID",
       "amount_cents": 1000,
       "note": "Test with wrong PIN"
     }'
   ```

**Expected Results**:
- ✅ First request returns 403 "Users can only create money moves for themselves"
- ✅ Second request returns 403 "Invalid user PIN"

### Scenario 4: UI Behavior Verification (Users Page vs Dashboard)

**Objective**: Verify UI behaves correctly across different user contexts

**Steps**:
1. Navigate to Dashboard, select User A, verify PIN and observe Top Up button
2. Return (deselect), select User B, verify PIN, observe same flow (button only after each user’s PIN)
3. Navigate to Users page – ensure per-row top-up (if retained) still enforces PIN before mutation (or is removed if design migrated fully to Dashboard)
4. As treasurer on Dashboard selecting another user: Top Up still available (treasurer path) but requires treasurer PIN in modal if acting on behalf (design dependent – verify implementation)
5. Ensure no residual session persists when switching users – each user selection demands its own PIN

**Expected Results**:
- ✅ Button visibility changes based on current user
- ✅ Other users can't see each other's "Top Up Balance" buttons
- ✅ Treasurers don't see "Top Up Balance" buttons (they use treasurer flow)
- ✅ Existing functionality unchanged

### Scenario 5: Error Handling

**Objective**: Verify error scenarios are handled gracefully

**Steps**:
1. Create money move request via Dashboard self flow
2. Disconnect network during modal submission
3. Verify error message displayed
4. Retry with network restored
5. Try submitting with invalid amount (negative, zero, non-numeric)
6. Try submitting without PIN
7. Try with inactive user account

**Expected Results**:
- ✅ Network errors shown to user
- ✅ Form validation prevents invalid submissions  
- ✅ PIN required for all submissions
- ✅ Inactive users cannot create requests
- ✅ Errors don't crash the application

## API Testing with curl

### Create User Money Move Request
```bash
curl -X POST http://localhost:8000/money-moves/user-request \
  -H "Content-Type: application/json" \
  -H "x-actor-id: <USER_UUID>" \
  -H "x-actor-pin: <USER_PIN>" \
  -d '{
    "type": "deposit",
    "user_id": "<SAME_USER_UUID>", 
    "amount_cents": 1500,
    "note": "Manual test deposit"
  }'
```

### List Pending Money Moves
```bash
curl http://localhost:8000/money-moves/pending
```

### Confirm Money Move (as treasurer)
```bash
curl -X PATCH http://localhost:8000/money-moves/<MOVE_ID>/confirm \
  -H "x-actor-id: <TREASURER_UUID>" \
  -H "x-actor-pin: <TREASURER_PIN>"
```

## Database Verification

Check the database directly to verify data integrity:

```sql
-- Check money move was created correctly
SELECT * FROM money_moves ORDER BY created_at DESC LIMIT 5;

-- Verify audit trail
SELECT * FROM audit WHERE entity = 'money_move' ORDER BY at DESC LIMIT 5;

-- Check user balance calculation
SELECT 
  u.display_name,
  COALESCE(SUM(CASE WHEN mm.type = 'deposit' AND mm.status = 'confirmed' THEN mm.amount_cents ELSE 0 END), 0) -
  COALESCE(SUM(CASE WHEN mm.type = 'payout' AND mm.status = 'confirmed' THEN mm.amount_cents ELSE 0 END), 0) -
  COALESCE(SUM(c.amount_cents), 0) as balance_cents
FROM users u
LEFT JOIN money_moves mm ON u.id = mm.user_id
LEFT JOIN consumptions c ON u.id = c.user_id  
GROUP BY u.id, u.display_name;
```

## Regression Testing

Verify existing functionality still works:

1. **Treasurer Money Moves**: Treasurers can still create money moves via treasurer dashboard
2. **Confirmation Flow**: Two-person confirmation still enforced
3. **Dashboard**: User dashboard still shows pending moves correctly
4. **Kiosk Mode**: Product consumption still works normally
5. **Balance Calculations**: Balance display remains accurate

## Performance Testing

For production readiness:

1. Create multiple concurrent user requests
2. Verify database transactions handle concurrency
3. Check API response times under load
4. Verify PIN verification performance
5. Test with large numbers of pending moves

## Accessibility Testing

1. Test with screen reader for button visibility
2. Verify keyboard navigation works
3. Check color contrast for new buttons
4. Test on mobile devices
5. Verify translations work correctly (German/English)

## Sign-off Checklist

- [ ] All test scenarios pass
- [ ] API endpoints respond correctly  
- [ ] Security constraints enforced
- [ ] UI behaves as expected
- [ ] Error handling works properly
- [ ] Existing functionality unaffected
- [ ] Database integrity maintained
- [ ] Audit trail properly recorded
- [ ] Translations display correctly
- [ ] Performance is acceptable

## Troubleshooting

### Common Issues:

1. **"Top Up Balance" button not visible**: Ensure user PIN has been verified (inline panel must disappear)
2. **PIN verification fails**: Verify correct PIN; user must be active
3. **403 errors**: For self-service ensure user_id matches actor header; for treasurer path ensure role is treasurer
4. **Modal doesn't open**: Check for JavaScript console errors
5. **Treasurer can't confirm**: Verify treasurer has correct role and PIN

### Debug Steps:

1. Check browser console for JavaScript errors
2. Check backend logs for API errors
3. Verify database contains expected data
4. Test API endpoints directly with curl
5. Check user roles and permissions in database