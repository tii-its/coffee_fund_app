# Manual Testing Guide: User-Initiated Money Moves

## Prerequisites
1. Development environment running (`make dev`)
2. Database migrated (`make migrate`) 
3. At least one admin, one treasurer, and one regular user created

## Test Scenarios

### Scenario 1: Basic User Money Move Creation

**Objective**: Verify users can create money moves for themselves

**Steps**:
1. Navigate to the Users page (`/users`)
2. Log in with a regular user account
3. Locate your user row in the table
4. Verify you see "Top Up Balance" button only on your row (not others)
5. Click "Top Up Balance" button
6. Fill in the modal:
   - Amount: €10.00
   - Note: "Test user-initiated deposit"
7. Submit the form
8. Verify PIN prompt appears
9. Enter correct PIN
10. Verify success message appears
11. Verify modal closes

**Expected Results**:
- ✅ Button only visible on current user's row
- ✅ Modal opens correctly  
- ✅ PIN verification required
- ✅ Success notification shown
- ✅ Money move created with "pending" status

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

### Scenario 4: UI Behavior Verification

**Objective**: Verify UI behaves correctly across different user contexts

**Steps**:
1. Log in as User A
2. Navigate to Users page
3. Verify "Top Up Balance" button only on User A's row
4. Log out and log in as User B  
5. Navigate to Users page
6. Verify "Top Up Balance" button only on User B's row (not User A's)
7. Log in as treasurer
8. Navigate to Users page
9. Verify admin/edit buttons work normally
10. Verify treasurer can see all users but no "Top Up Balance" buttons

**Expected Results**:
- ✅ Button visibility changes based on current user
- ✅ Other users can't see each other's "Top Up Balance" buttons
- ✅ Treasurers don't see "Top Up Balance" buttons (they use treasurer flow)
- ✅ Existing functionality unchanged

### Scenario 5: Error Handling

**Objective**: Verify error scenarios are handled gracefully

**Steps**:
1. Create money move request as user
2. Disconnect network during submission
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

1. **"Top Up Balance" button not visible**: Check if user is logged in and viewing their own row
2. **PIN verification fails**: Verify PIN is correct and user is active
3. **403 errors**: Check user is trying to create move for themselves only
4. **Modal doesn't open**: Check for JavaScript console errors
5. **Treasurer can't confirm**: Verify treasurer has correct role and PIN

### Debug Steps:

1. Check browser console for JavaScript errors
2. Check backend logs for API errors
3. Verify database contains expected data
4. Test API endpoints directly with curl
5. Check user roles and permissions in database