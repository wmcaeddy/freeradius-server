# Local Development Guide

This guide helps you run the FreeRADIUS + PrivacyIDEA services locally using Docker Compose.

## Quick Start

1. **Copy environment variables**:
   ```bash
   cp .env.example .env
   ```

2. **Build and start services**:
   ```bash
   docker-compose up --build
   ```

3. **Access services**:
   - PrivacyIDEA Web Interface: http://localhost:8080
   - FreeRADIUS RADIUS Server: localhost:1812 (UDP)

## Service URLs

- **PrivacyIDEA Web**: http://localhost:8080
- **PrivacyIDEA API**: http://localhost:8080/validate/check
- **FreeRADIUS Auth**: localhost:1812/udp
- **FreeRADIUS Accounting**: localhost:1813/udp
- **FreeRADIUS Status**: localhost:18120/tcp

## Default Credentials

### PrivacyIDEA Admin
- Username: `admin`
- Password: `admin123` (from .env)

### Demo Users (Auto-created)
- `demo` - HOTP/TOTP tokens
- `vasco_demo` - Vasco token  
- `testuser` - HOTP token

## Testing

### Health Checks
```bash
# PrivacyIDEA health
curl http://localhost:8080/health

# FreeRADIUS status
echo "Message-Authenticator = 0x00" | radclient -x localhost:18120 status adminsecret
```

### RADIUS Authentication
```bash
# Install FreeRADIUS client tools
sudo apt-get install freeradius-utils

# Test authentication
radtest demo 755224 localhost 0 testing123
radtest vasco_demo 123456 localhost 0 testing123
```

## Development Commands

### Start services
```bash
docker-compose up --build
```

### Start in background
```bash
docker-compose up -d --build
```

### Stop services
```bash
docker-compose down
```

### View logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f privacyidea
docker-compose logs -f freeradius
```

### Restart a service
```bash
docker-compose restart privacyidea
docker-compose restart freeradius
```

### Rebuild a service
```bash
docker-compose up --build privacyidea
docker-compose up --build freeradius
```

## Volumes and Data

### Data Persistence
- **PrivacyIDEA data**: Docker volume `privacyidea-data`
- **FreeRADIUS data**: Docker volume `freeradius-data`

### Access volume data
```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect freeradius-server_privacyidea-data

# Access volume data
docker run --rm -v freeradius-server_privacyidea-data:/data alpine ls -la /data
```

## Configuration

### Environment Variables
Edit `.env` file to customize:
- Service ports
- Database connections
- Debug settings
- Security keys

### Service Configuration
- **PrivacyIDEA**: `privacyidea-service/config/`
- **FreeRADIUS**: `freeradius-service/config/`

## Troubleshooting

### Common Issues

1. **Port conflicts**
   ```bash
   # Check if ports are in use
   sudo netstat -tulpn | grep :1812
   sudo netstat -tulpn | grep :8080
   ```

2. **Permission errors**
   ```bash
   # Reset volumes
   docker-compose down -v
   docker-compose up --build
   ```

3. **Service startup failures**
   ```bash
   # Check logs
   docker-compose logs privacyidea
   docker-compose logs freeradius
   ```

### Debug Mode
Enable debug logging by setting in `.env`:
```
PI_DEBUG=true
PRIVACYIDEA_DEBUG=true
```

### Clean Reset
```bash
# Remove all containers, volumes, and images
docker-compose down -v --rmi all
docker-compose up --build
```

## Development Workflow

1. **Make code changes**
2. **Rebuild affected service**:
   ```bash
   docker-compose up --build [service-name]
   ```
3. **Test changes**
4. **Commit changes**:
   ```bash
   git add .
   git commit -m "Description of changes"
   ```

## Testing with Demo Tokens

### Vasco Demo Tokens
Get demo tokens from: https://gs.onespan.cloud/te-demotokens/go6

### Test Authentication Flow
1. **Set up token in PrivacyIDEA**:
   - Access http://localhost:8080
   - Login as admin
   - Create user and assign token

2. **Test RADIUS authentication**:
   ```bash
   radtest username token_value localhost 0 testing123
   ```

## Integration Testing

### Test Service Communication
```bash
# Test PrivacyIDEA API directly
curl -X POST http://localhost:8080/validate/check \
  -d "user=demo&pass=123456"

# Test FreeRADIUS to PrivacyIDEA communication
radtest demo 123456 localhost 0 testing123
```

## Production Considerations

Before deploying to production:
1. Change default passwords in `.env`
2. Use strong secret keys
3. Enable SSL/TLS
4. Configure external databases
5. Set up monitoring and logging

## Support

Check logs first:
```bash
docker-compose logs -f
```

For issues:
1. Verify environment variables
2. Check service health
3. Review inter-service communication
4. Consult DEPLOYMENT-GUIDE.md for Railway deployment