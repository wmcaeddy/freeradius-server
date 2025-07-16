# PrivacyIDEA Testing Users

## Available Users for Testing (Port 5002)

### Primary Testing User
- **Username**: `eddy`
- **Realm**: Default realm
- **Resolver**: deflocal (local system users)

### Alternative Testing Users
- **Username**: `root`
- **Realm**: Default realm
- **Resolver**: deflocal

- **Username**: `freerad`
- **Realm**: Default realm
- **Resolver**: deflocal

## Testing Information

### PrivacyIDEA Web Interface
- **URL**: http://0.0.0.0:5002
- **Login**: Use any of the above usernames
- **OTP Testing**: 
  - OTP 324922: ✅ Verified
  - OTP 412020: ✅ Verified

### Custom Web Page
- **URL**: http://0.0.0.0:5001
- **Service**: User-built web application

## Recommended Testing Approach

1. **Primary User**: Use `eddy` for main testing
2. **Backup User**: Use `root` if needed
3. **Service User**: Use `freerad` for FreeRADIUS integration testing

## OTP Testing Commands

```bash
# Test OTP 324922 with user 'eddy'
python verify_otp_324922.py

# Test OTP 412020 with user 'eddy'  
python verify_otp_412020.py

# Test via web interface
# Navigate to http://0.0.0.0:5002
# Username: eddy
# OTP: 324922 or 412020
```

## Note
The users are loaded from the local system (`/etc/passwd`) via the `deflocal` resolver, so any valid system user can be used for testing.