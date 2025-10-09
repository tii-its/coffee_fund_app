# User-Initiated Money Move Implementation

## Overview

This document describes the implementation of user-initiated money moves, allowing users to request money transfers for their own accounts directly from the Users page in the dashboard.

## Problem Statement

Previously, only treasurers could create money moves for any user. The requirement was to allow regular users to initiate money moves for themselves, maintaining the two-person confirmation rule where a treasurer must still confirm the request.

## Architecture

### Backend Implementation

#### New Endpoint
- **Route**: `POST /money-moves/user-request`
- **Purpose**: Allow users to create money move requests for themselves
- **Authentication**: Requires valid user PIN verification

#### New Dependency Function
```python
def user_actor(
    actor_id: UUID = Header(..., alias="x-actor-id"),
    actor_pin: str = Header(..., alias="x-actor-pin"),
    db: Session = Depends(get_db)
):
    """Dependency ensuring the supplied actor is a valid user with correct PIN."""
```

This function:
- Validates the user exists and is active
- Verifies the user's PIN
- Does not require treasurer role (unlike existing `treasurer_actor`)

#### Security Constraints
1. **Self-Only Rule**: Users can only create money moves for themselves
   ```python
   if money_move.user_id != user_requesting.id:
       raise HTTPException(status_code=403, detail="Users can only create money moves for themselves")
   ```

2. **Active User Check**: Inactive users cannot create money moves
3. **PIN Verification**: All requests require valid PIN authentication
4. **Two-Person Confirmation**: User-created money moves still require treasurer confirmation

### Frontend Implementation

#### Users Page Enhancement
- Added "Top Up Balance" button visible only for current user's row
- Integrated existing `TopUpBalanceModal` component
- Uses `usePerActionPin` hook for PIN verification

#### API Client Update
```typescript
createUserRequest: (moneyMove: MoneyMoveCreate, actor: ActorHeaders) =>
  api.post<MoneyMove>('/money-moves/user-request', moneyMove, withActor({}, actor)),
```

#### User Experience Flow
1. User navigates to Users page
2. User sees "Top Up Balance" button only on their own row
3. User clicks button to open modal
4. User fills out amount and optional note
5. System prompts for PIN verification
6. Money move request is created with "pending" status
7. Treasurer can later confirm/reject the request

## Technical Details

### Database Schema
No changes to existing schema. User-created money moves use the same `money_moves` table with:
- `created_by` = user who created the request
- `status` = "pending" (awaiting treasurer confirmation)
- `confirmed_by` = null (until treasurer acts)

### Status Flow
1. **User Creates**: `status = "pending"`, `created_by = user_id`
2. **Treasurer Confirms**: `status = "confirmed"`, `confirmed_by = treasurer_id`, `confirmed_at = timestamp`
3. **Treasurer Rejects**: `status = "rejected"`, `confirmed_by = treasurer_id`, `confirmed_at = timestamp`

### Error Handling
- **403 Forbidden**: User tries to create money move for another user
- **403 Forbidden**: Invalid PIN or inactive user
- **404 Not Found**: User not found

## Testing

### Backend Tests
Located in: `backend/app/tests/test_money_moves_api.py`

Test cases:
- `test_create_user_money_move_request_deposit`: Successful deposit request
- `test_create_user_money_move_request_payout`: Successful payout request
- `test_create_user_money_move_request_for_other_user_forbidden`: Security constraint
- `test_create_user_money_move_request_invalid_pin`: PIN validation
- `test_create_user_money_move_request_inactive_user`: Active user requirement
- `test_user_created_money_move_can_be_confirmed_by_treasurer`: Integration test

### Frontend Tests
Located in: `frontend/src/__tests__/user-money-move.test.tsx`

Test cases:
- Button visibility (only for current user)
- Modal opening behavior
- PIN verification requirement
- Error handling
- Integration with existing components

## Configuration

No new configuration variables required. Uses existing PIN and authentication infrastructure.

## Deployment Notes

### Database Migration
No database migration required - uses existing tables and relationships.

### API Versioning
New endpoint is additive and doesn't break existing functionality.

### Rollback Plan
If needed, the new endpoint can be disabled by removing the route, with no impact on existing treasurer-initiated money moves.

## Security Considerations

1. **Principle of Least Privilege**: Users can only act on their own accounts
2. **Two-Person Rule Maintained**: User creation + treasurer confirmation
3. **Audit Trail**: All actions logged with proper actor attribution
4. **PIN Protection**: Every action requires PIN re-verification
5. **Active User Check**: Deactivated users cannot create requests

## Future Enhancements

Potential improvements:
1. **Email Notifications**: Notify treasurers of pending user requests
2. **Request Limits**: Daily/weekly limits on user-initiated requests
3. **Auto-Approval**: For small amounts below a threshold
4. **Request Comments**: Allow treasurers to add comments when rejecting
5. **User Dashboard**: Show status of pending requests in user's dashboard

## Integration Points

### Existing Systems
- **Audit Service**: All actions properly logged
- **PIN Service**: Reuses existing PIN verification
- **Balance Service**: Integrates with existing balance calculations
- **Notification System**: Ready for future notification enhancements

### API Compatibility
- Existing treasurer endpoints unchanged
- New endpoint follows same patterns and conventions
- Response schemas consistent with existing money move API

## Monitoring and Metrics

Consider tracking:
- Number of user-initiated requests vs treasurer-initiated
- Request approval/rejection rates
- Average time from request to confirmation
- PIN failure rates for money move requests

This implementation provides a secure, user-friendly way for users to initiate money moves while maintaining all existing security and audit requirements.