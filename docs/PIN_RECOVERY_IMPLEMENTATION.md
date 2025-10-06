# PIN PIN Management / Reset (Revised)

## Overview

This document (revised) describes the current PIN management capabilities of the Coffee Fund Web App.

NOTE (2025-10-06): The previously implemented end‑user self "PIN Recovery" flow (separate from normal Change PIN) has been removed to reduce UX redundancy. Users can still:

1. Change their own PIN (requires current PIN) via the Change PIN modal.
2. Ask an admin to reset their PIN to the default (1234) if they have forgotten it.

The former Recover PIN modal (which duplicated Change PIN semantics) and its translations were removed. Backend endpoint `/users/{id}/recover-pin` is currently retained for possible future re‑activation (e.g. adding email-based verification) but is no longer surfaced in the UI.

## Requirements

Scope after simplification:
1. **User PIN Change** (self-service, requires current PIN)
2. **Admin PIN Reset** (forces default 1234, requires admin PIN)

## Implementation Architecture

### Backend Changes

#### 1. PIN Service (`backend/app/services/pin.py`)

Added new methods to the existing `PinService` class:

```python
@staticmethod
def reset_to_default_pin(user_id: UUID, db: Session) -> bool:
    """Reset user PIN to default '1234'"""
    return PinService.set_user_pin(user_id, "1234", db)

@staticmethod
def recover_user_pin(...):
  """(Legacy endpoint) Retained for potential future email-based recovery; not used by frontend."""
```

#### 2. API Schemas (`backend/app/schemas/users.py`)

```python
class PinResetRequest(BaseModel):
    """Admin request to reset user PIN to default"""
    pass  # Actor info comes from headers

class PinRecoveryRequest(BaseModel):  # Legacy / currently unused by UI
  new_pin: str
  verification_method: str
  verification_data: str
```

#### 3. New API Endpoints (`backend/app/api/users.py`)

**Admin PIN Reset:**
- `PUT /users/{user_id}/reset-pin`
- Requires admin role and PIN verification via headers
- Resets target user PIN to "1234"
- Full audit logging

**(Legacy) User PIN Recovery:**
- Endpoint retained (`POST /users/{user_id}/recover-pin`) but not exposed in UI.
- May be repurposed for future email-based reset flows.

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

### Frontend

Removed: `PinRecoveryModal.tsx` and associated dashboard button. Only `PinChangeModal` (self change) and admin reset button in `UserEditModal` remain.

#### 2. Enhanced User Edit Modal (`frontend/src/components/UserEditModal.tsx`)

Added PIN management section for admins:
- "PIN Management" section in edit form
- "Reset PIN to 1234" button
- Admin PIN confirmation via `usePerActionPin` hook
- Success/error feedback

#### Dashboard (`frontend/src/pages/Dashboard.tsx`)

When user views their own profile:
- "Change PIN" button (opens `PinChangeModal`).
- No separate recovery button (removed as redundant).

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

### 1. User PIN Change Flow

1. User selects themselves on Dashboard
2. Clicks "Change PIN"
3. Enters current PIN, new PIN, confirm new PIN
4. Validation (match, length >=4)
5. Backend `/users/change-user-pin` (current implementation) updates stored hash
6. Success feedback & audit log

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

### Email Verification (Future)
- Could re‑enable `/users/{id}/recover-pin` with email token

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

Current streamlined approach removes redundant user recovery path, simplifying UX while retaining secure self change + admin reset flows. Future enhancements (email / MFA) can reuse the dormant recovery endpoint.