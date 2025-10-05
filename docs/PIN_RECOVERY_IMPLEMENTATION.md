# PIN Recovery Implementation

## Overview

This document describes the implementation of PIN recovery functionality for the Coffee Fund Web App, allowing both user-initiated PIN recovery and admin PIN reset capabilities.

## Requirements

Based on the problem statement:
1. **User PIN Recovery**: Users shall be able to define a new PIN in dashboard when selecting themselves, with user confirmation required
2. **Admin PIN Reset**: Admin shall be able to reset any user's PIN to default (1234) in the Users page via edit button, with admin confirmation required

## Implementation Architecture

### Backend Changes

#### 1. Enhanced PIN Service (`backend/app/services/pin.py`)

Added new methods to the existing `PinService` class:

```python
@staticmethod
def reset_to_default_pin(user_id: UUID, db: Session) -> bool:
    """Reset user PIN to default '1234'"""
    return PinService.set_user_pin(user_id, "1234", db)

@staticmethod
def recover_user_pin(user_id: UUID, new_pin: str, verification_method: str, verification_data: str, db: Session) -> bool:
    """Recover user PIN with verification"""
    # Supports 'current_pin' verification method
    # Future: could add email verification
```

#### 2. New API Schemas (`backend/app/schemas/users.py`)

```python
class PinResetRequest(BaseModel):
    """Admin request to reset user PIN to default"""
    pass  # Actor info comes from headers

class PinRecoveryRequest(BaseModel):
    """User request to recover their PIN"""
    new_pin: str
    verification_method: str  # 'current_pin' or future: 'email' 
    verification_data: str   # the current PIN or email token
```

#### 3. New API Endpoints (`backend/app/api/users.py`)

**Admin PIN Reset:**
- `PUT /users/{user_id}/reset-pin`
- Requires admin role and PIN verification via headers
- Resets target user PIN to "1234"
- Full audit logging

**User PIN Recovery:**
- `POST /users/{user_id}/recover-pin`
- Accepts current PIN verification
- Sets new PIN after verification
- Self-service audit logging

#### 4. Enhanced API Client (`frontend/src/api/client.ts`)

Added missing and new methods to `usersApi`:
```typescript
// Fixed missing methods
verifyPin: (user_id: string, pin: string) => Promise<{message: string}>
changePin: (current_pin: string, new_pin: string, actor_id?: string) => Promise<{message: string}>

// New PIN recovery methods
resetPin: (user_id: string, actor: ActorHeaders) => Promise<{message: string}>
recoverPin: (user_id: string, new_pin: string, verification_method: string, verification_data: string) => Promise<{message: string}>
```

### Frontend Changes

#### 1. PIN Recovery Modal (`frontend/src/components/PinRecoveryModal.tsx`)

New component for user-initiated PIN recovery:
- Requires current PIN verification
- PIN confirmation with validation
- Integration with existing API patterns
- Comprehensive error handling

#### 2. Enhanced User Edit Modal (`frontend/src/components/UserEditModal.tsx`)

Added PIN management section for admins:
- "PIN Management" section in edit form
- "Reset PIN to 1234" button
- Admin PIN confirmation via `usePerActionPin` hook
- Success/error feedback

#### 3. Enhanced Dashboard (`frontend/src/pages/Dashboard.tsx`)

When user views their own profile:
- "Change PIN" button (existing `PinChangeModal`)
- "Recover PIN" button (new `PinRecoveryModal`)
- Only shown when `currentUser.id === selectedUser.id`

#### 4. Internationalization

Added translations for German and English:
```json
{
  "pin": {
    "recoverPin": "Recover PIN / PIN wiederherstellen",
    "recoverPinTitle": "Recover PIN for {{name}} / PIN für {{name}} wiederherstellen",
    "recoverPinDescription": "Enter your current PIN to set a new PIN",
    "pinManagement": "PIN Management / PIN-Verwaltung", 
    "resetToDefault": "Reset PIN to 1234 / PIN auf 1234 zurücksetzen",
    "resetSuccess": "PIN successfully reset to 1234",
    // ... additional translations
  }
}
```

## User Flows

### 1. User PIN Recovery Flow

**Trigger:** User selects themselves in Dashboard and clicks "Recover PIN"

1. Dashboard → User selects self → Shows PIN management buttons
2. User clicks "Recover PIN" → `PinRecoveryModal` opens
3. User enters:
   - Current PIN (verification)
   - New PIN 
   - Confirm new PIN
4. Frontend validates PIN format and matching
5. API call to `/users/{user_id}/recover-pin` with current PIN verification
6. Backend verifies current PIN and sets new PIN
7. Success feedback and audit log entry
8. Modal closes

**Security:** Requires current PIN, self-service only, full audit trail

### 2. Admin PIN Reset Flow  

**Trigger:** Admin clicks "Edit" on any user in Users page

1. Users page → Admin clicks "Edit" → `UserEditModal` opens
2. Modal shows "PIN Management" section with reset button
3. Admin clicks "Reset PIN to 1234" → `PerActionPinModal` opens
4. Admin selects themselves and enters admin PIN
5. API call to `/users/{user_id}/reset-pin` with admin verification
6. Backend verifies admin credentials and resets PIN to "1234" 
7. Success message: "PIN successfully reset to 1234"
8. Audit log entry with admin actor

**Security:** Requires admin role, admin PIN confirmation, audit trail

## Security Considerations

### Authentication & Authorization
- User PIN recovery: Self-service only (user must verify current PIN)
- Admin PIN reset: Requires admin role + admin PIN verification
- All operations use existing `PerActionPin` infrastructure

### Audit Trail
All PIN operations logged with:
- Actor ID (self for recovery, admin for reset)
- Action type (`recover_pin` or `reset_pin`)
- Target user information
- Timestamp and metadata

### Data Protection
- PIN hashing via SHA256 (existing `PinService.hash_pin`)
- No plaintext PIN storage
- Default PIN clearly communicated after reset

## Technical Patterns

### Following Existing Conventions
- Uses existing `usePerActionPin` hook for admin operations
- Follows established modal component patterns
- Leverages existing API client structure
- Maintains audit logging consistency
- Uses established i18n translation patterns

### Error Handling
- Frontend form validation with user feedback
- Backend HTTP status codes (403 for invalid PIN, 404 for user not found)
- Comprehensive error messages in multiple languages
- Loading states and disabled buttons during operations

## Testing Approach

### Backend Testing
- Unit tests for `PinService` new methods
- Integration tests for new API endpoints
- Test PIN verification edge cases
- Verify audit logging

### Frontend Testing  
- Component tests for new modals
- Integration tests for user flows
- PIN validation testing
- Error state handling

### Manual Testing
1. **User PIN Recovery:**
   - Self-select in dashboard → verify PIN buttons appear
   - Test correct/incorrect current PIN scenarios
   - Verify new PIN validation rules
   - Check audit logs

2. **Admin PIN Reset:**
   - Edit user as admin → verify reset section appears  
   - Test admin PIN confirmation flow
   - Verify target user PIN reset to "1234"
   - Check admin audit trail

## Future Enhancements

### Email Verification
- Add email-based PIN recovery option
- Email token generation and verification
- Fallback when current PIN is forgotten

### Additional Security
- Rate limiting for PIN attempts
- Account lockout after failed attempts  
- PIN complexity requirements
- PIN expiration policies

### User Experience
- SMS-based PIN recovery
- Security questions as alternative verification
- PIN history (prevent reuse)
- Multi-factor authentication integration

## Deployment Notes

### Environment Variables
No new environment variables required. Uses existing PIN hashing and authentication infrastructure.

### Database Changes
No database schema changes required. Uses existing `pin_hash` field in users table.

### Dependencies  
No new dependencies added. Uses existing React Query, i18next, and FastAPI patterns.

## Conclusion

This implementation provides comprehensive PIN recovery functionality while maintaining security best practices and following existing codebase patterns. The solution addresses both user self-service and admin management scenarios with proper verification and audit trails.