# Separated FreeRADIUS + PrivacyIDEA Deployment Guide

This guide explains how to deploy FreeRADIUS and PrivacyIDEA as separate, connected services on Railway.com with consistent volumes.

## Architecture Overview

### Service Architecture
```
┌─────────────────┐    HTTP/REST API    ┌─────────────────┐
│   FreeRADIUS    │ ──────────────────► │   PrivacyIDEA   │
│   Service       │                     │   Service       │
│                 │                     │                 │
│ - RADIUS Auth   │                     │ - Token Mgmt    │
│ - Port 1812     │                     │ - Web UI        │
│ - Port 1813     │                     │ - REST API      │
│ - Volume: /app  │                     │ - Volume: /app  │
└─────────────────┘                     └─────────────────┘
```

### Benefits of Separation
- **Independent scaling**: Scale each service based on load
- **Isolated failures**: If one service fails, the other continues
- **Easier maintenance**: Update/restart services independently
- **Better resource utilization**: Optimize resources per service
- **Persistent data**: Each service has its own consistent volume

## Quick Deployment

### Prerequisites
1. **Railway CLI installed**:
   ```bash
   curl -fsSL https://railway.com/install.sh | sh
   ```

2. **Railway login**:
   ```bash
   railway login
   ```

### Automated Deployment
```bash
# Make script executable
chmod +x deploy-separated-services.sh

# Run deployment script
./deploy-separated-services.sh
```

## Manual Deployment

### Step 1: Deploy PrivacyIDEA Service

1. **Navigate to PrivacyIDEA service directory**:
   ```bash
   cd privacyidea-service
   ```

2. **Create new Railway project**:
   ```bash
   railway init
   ```

3. **Set environment variables**:
   ```bash
   railway variables set PI_SECRET_KEY="your-super-secret-key-here"
   railway variables set PI_PEPPER="your-pepper-here"
   railway variables set PI_ADMIN_PASSWORD="your-admin-password"
   ```

4. **Deploy**:
   ```bash
   railway up
   ```

5. **Get service URL**:
   ```bash
   railway status
   ```

### Step 2: Deploy FreeRADIUS Service

1. **Navigate to FreeRADIUS service directory**:
   ```bash
   cd ../freeradius-service
   ```

2. **Create new Railway project**:
   ```bash
   railway init
   ```

3. **Set environment variables**:
   ```bash
   railway variables set PRIVACYIDEA_URL="https://your-privacyidea-service.railway.app"
   railway variables set RADIUS_CLIENT_SECRET="your-radius-secret"
   ```

4. **Deploy**:
   ```bash
   railway up
   ```

## Configuration

### Environment Variables

#### PrivacyIDEA Service
| Variable | Description | Required |
|----------|-------------|----------|
| `PI_SECRET_KEY` | Secret key for sessions | Yes |
| `PI_PEPPER` | Encryption pepper | Yes |
| `PI_ADMIN_PASSWORD` | Admin user password | Yes |
| `DATABASE_URL` | External database URL | No |
| `REDIS_URL` | External Redis URL | No |

#### FreeRADIUS Service
| Variable | Description | Required |
|----------|-------------|----------|
| `PRIVACYIDEA_URL` | PrivacyIDEA service URL | Yes |
| `RADIUS_CLIENT_SECRET` | RADIUS client secret | Yes |
| `PRIVACYIDEA_VALIDATE_SSL` | SSL validation | No |
| `PRIVACYIDEA_REALM` | Default realm | No |
| `PRIVACYIDEA_DEBUG` | Debug mode | No |

### Service URLs

After deployment, you'll get:
- **PrivacyIDEA Web Interface**: `https://privacyidea-production.railway.app`
- **FreeRADIUS RADIUS Server**: `radius-server.railway.app:1812`

## Volume Consistency

### PrivacyIDEA Volume (`/app/data`)
- **Database**: `/app/data/privacyidea/privacyidea.db`
- **Encryption keys**: `/app/data/privacyidea/enckey`
- **Audit keys**: `/app/data/privacyidea/private.pem`, `/app/data/privacyidea/public.pem`

### FreeRADIUS Volume (`/app/data`)
- **Logs**: `/app/data/freeradius/logs/`
- **Configuration**: `/app/data/freeradius/config/`
- **Certificates**: `/app/data/freeradius/certs/`

## Inter-Service Communication

### How FreeRADIUS Connects to PrivacyIDEA
1. **Authentication Request**: Client sends RADIUS auth to FreeRADIUS
2. **Token Validation**: FreeRADIUS calls PrivacyIDEA REST API
3. **Response**: PrivacyIDEA validates token and returns result
4. **RADIUS Response**: FreeRADIUS sends Access-Accept/Reject to client

### API Endpoints Used
- **Token Validation**: `POST /validate/check`
- **Health Check**: `GET /health`

## Demo Token Setup

### 1. Access PrivacyIDEA Web Interface
- URL: `https://your-privacyidea-service.railway.app`
- Credentials: `admin` / `your-admin-password`

### 2. Demo Users Created Automatically
- **demo**: HOTP/TOTP tokens
- **vasco_demo**: Vasco token
- **testuser**: HOTP token

### 3. Test Authentication
```bash
# Test with radtest (install freeradius-utils)
radtest demo 755224 your-freeradius-server.railway.app 0 your-radius-secret
```

## Testing

### Health Checks
```bash
# PrivacyIDEA health
curl https://your-privacyidea-service.railway.app/health

# FreeRADIUS status (requires radclient)
echo "Message-Authenticator = 0x00" | radclient -x your-freeradius-server.railway.app:18120 status adminsecret
```

### RADIUS Authentication
```bash
# Test RADIUS authentication
radtest demo 755224 your-freeradius-server.railway.app 0 your-radius-secret

# Test with different users
radtest vasco_demo 123456 your-freeradius-server.railway.app 0 your-radius-secret
radtest testuser 287082 your-freeradius-server.railway.app 0 your-radius-secret
```

## Monitoring

### Logs
```bash
# PrivacyIDEA logs
cd privacyidea-service
railway logs

# FreeRADIUS logs
cd freeradius-service
railway logs
```

### Metrics
- **PrivacyIDEA**: Web interface shows authentication statistics
- **FreeRADIUS**: RADIUS accounting logs track usage
- **Railway**: Built-in metrics for CPU, memory, and network

## Troubleshooting

### Common Issues

1. **Connection timeout between services**
   - Check `PRIVACYIDEA_URL` is correct
   - Verify SSL settings match

2. **Authentication failures**
   - Check demo tokens are set up in PrivacyIDEA
   - Verify realm configuration

3. **Service startup failures**
   - Check environment variables are set
   - Review service logs for errors

### Debug Mode
Enable debug logging:
```bash
railway variables set PRIVACYIDEA_DEBUG=true
```

### Service Restart
```bash
# Restart individual services
railway service restart
```

## Scaling

### Vertical Scaling
- Increase memory/CPU per service in Railway dashboard

### Horizontal Scaling
- Deploy multiple FreeRADIUS instances (stateless)
- Use external database for PrivacyIDEA for multiple instances

## Security

### Production Considerations
1. **Strong secrets**: Use strong, unique secrets for all services
2. **SSL/TLS**: Enable SSL validation in production
3. **Network isolation**: Use private networking when available
4. **Regular updates**: Keep services updated
5. **Monitoring**: Set up alerts for authentication failures

## Backup

### Database Backup
```bash
# Download PrivacyIDEA database
railway service connect privacyidea
sqlite3 /app/data/privacyidea/privacyidea.db .dump > backup.sql
```

### Configuration Backup
- Export PrivacyIDEA configuration via web interface
- Store FreeRADIUS configuration in version control

## Support

### Resources
- [PrivacyIDEA Documentation](https://privacyidea.readthedocs.io/)
- [FreeRADIUS Documentation](https://freeradius.org/documentation/)
- [Railway Documentation](https://docs.railway.app/)

### Getting Help
- Check service logs first
- Verify environment variables
- Test connectivity between services
- Review this deployment guide