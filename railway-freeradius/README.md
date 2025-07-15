# FreeRADIUS with PrivacyIDEA for Railway.com

This project provides a complete containerized authentication solution with FreeRADIUS and PrivacyIDEA integration, specifically designed for deployment on Railway.com with support for Vasco demo tokens.

## Architecture

### Components

1. **PrivacyIDEA Server**
   - Complete token management system
   - Web UI for administration
   - Support for HOTP, TOTP, and Vasco tokens
   - SQLite database with persistent storage
   - Nginx reverse proxy

2. **Primary RADIUS Server**
   - FreeRADIUS 3.2.3 with PrivacyIDEA integration
   - Python-based authentication module
   - Supports Vasco demo tokens via https://gs.onespan.cloud/te-demotokens/go6
   - Handles authentication on port 1812

3. **Proxy RADIUS Server**
   - Routes requests to multiple backend servers
   - Implements "first positive response wins" logic
   - Provides failover between backends
   - Handles authentication on port 11812

### File Structure

```
railway-freeradius/
├── Dockerfile                 # Multi-stage Docker build for FreeRADIUS
├── docker-compose.yml         # Local development setup
├── railway.toml              # Railway.com deployment config
├── .env.example              # Environment variables template
├── config/                   # FreeRADIUS configuration
│   ├── radiusd.conf          # Main server configuration
│   ├── mods-available/       # Available modules
│   └── sites-available/      # Virtual server configs
├── privacyidea/              # PrivacyIDEA server
│   ├── Dockerfile            # PrivacyIDEA container
│   ├── config/               # PrivacyIDEA configuration
│   ├── init/                 # Initialization scripts
│   └── nginx/                # Nginx configuration
├── scripts/                  # Python modules and scripts
│   ├── docker-entrypoint.sh  # Container startup script
│   ├── privacyidea_auth.py   # PrivacyIDEA authentication
│   ├── proxy_loadbalance.py  # Proxy load balancing
│   └── setup-demo-tokens.py  # Demo token setup
└── test-radius.sh            # Testing script
```

## Deployment

### Railway.com Deployment

1. **Set up environment variables in Railway:**
   ```bash
   # PrivacyIDEA Server Configuration
   PI_SECRET_KEY=your-super-secret-key-here-make-it-long-and-random
   PI_PEPPER=your-pepper-here-also-make-it-random
   PI_ADMIN_PASSWORD=your-admin-password
   
   # FreeRADIUS Configuration
   PRIVACYIDEA_URL=http://privacyidea:80
   PRIVACYIDEA_VALIDATE_SSL=false
   PRIVACYIDEA_REALM=default
   
   # Secrets (use Railway's secret management)
   RADIUS_CLIENT_SECRET=your-client-secret
   BACKEND1_SECRET=backend1-secret
   BACKEND2_SECRET=backend2-secret
   
   # Backend servers
   BACKEND1_HOST=freeradius-privacyidea
   BACKEND2_HOST=your-second-radius-server.com
   ```

2. **Deploy to Railway:**
   ```bash
   railway login
   railway init
   railway up
   ```

3. **Volume Configuration:**
   - Persistent data is stored in `/app/data`
   - Railway.com automatically provisions the volume
   - Certificates and logs are persisted across restarts

### Local Development

1. **Prerequisites:**
   ```bash
   # Install Docker and Docker Compose
   sudo apt-get install docker.io docker-compose
   
   # Install RADIUS testing tools
   sudo apt-get install freeradius-utils
   ```

2. **Setup:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   
   docker-compose up -d
   ```

3. **Initialize demo tokens:**
   ```bash
   # Wait for PrivacyIDEA to be ready
   docker-compose logs -f privacyidea
   
   # Set up demo tokens
   docker-compose exec privacyidea python3 /usr/local/bin/setup-demo-tokens.py
   ```

4. **Testing:**
   ```bash
   ./test-radius.sh
   ```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PI_SECRET_KEY` | PrivacyIDEA server secret key | `your-secret-key-here` |
| `PI_PEPPER` | PrivacyIDEA encryption pepper | `your-pepper-here` |
| `PI_ADMIN_PASSWORD` | Admin user password | `admin` |
| `PRIVACYIDEA_URL` | PrivacyIDEA server URL | `http://privacyidea:80` |
| `PRIVACYIDEA_VALIDATE_SSL` | Validate SSL certificates | `false` |
| `PRIVACYIDEA_REALM` | Default realm for authentication | `default` |
| `RADIUS_CLIENT_SECRET` | Shared secret for RADIUS clients | `testing123` |
| `BACKEND1_HOST` | Primary backend server | `freeradius-privacyidea` |
| `BACKEND2_HOST` | Secondary backend server | `` |
| `PROXY_BACKENDS` | JSON array of backend configurations | `[]` |

### PrivacyIDEA Web Interface

Access the PrivacyIDEA web interface at `http://localhost:80` (or your deployed URL):

- **Default Admin Credentials:** `admin` / `admin` (change in production!)
- **Features:**
  - User management
  - Token enrollment and management
  - Policy configuration
  - Audit logs
  - System configuration

### Demo Users and Tokens

The system creates demo users during initialization:

- **demo**: HOTP/TOTP tokens for testing
- **vasco_demo**: Vasco demo token integration
- **testuser**: Standard HOTP token

### Vasco Demo Token Support

The system is pre-configured to work with Vasco demo tokens:

- Demo URL: https://gs.onespan.cloud/te-demotokens/go6
- Use username `vasco_demo` for demo token testing
- The PrivacyIDEA integration will handle the token validation

### Proxy Configuration

The proxy server implements special logic where:
- Requests are sent to multiple backend servers
- If ANY backend returns Access-Accept, the proxy returns Access-Accept
- This provides redundancy and failover capability

## Testing

### Manual Testing

```bash
# Test direct authentication with demo tokens
radtest demo 755224 localhost 0 testing123 -P 1812

# Test proxy authentication
radtest demo 755224 localhost 0 testing123 -P 11812

# Test Vasco demo token
radtest vasco_demo 123456 localhost 0 testing123 -P 1812

# Test via PrivacyIDEA web interface
curl -X POST http://localhost:80/validate/check \
  -d "user=demo&pass=755224&realm=default"
```

### Automated Testing

```bash
# Run the test script
./test-radius.sh

# Test specific scenarios
RADIUS_HOST=your-railway-app.railway.app ./test-radius.sh
```

## Monitoring

### Health Checks

- Railway.com health checks are configured for port 1812
- Status server is available on port 18120
- Logs are available in `/var/log/radius/`

### Log Locations

- **FreeRADIUS logs:** `/var/log/radius/radius.log`
- **PrivacyIDEA logs:** `/var/log/privacyidea/privacyidea.log`
- **Nginx logs:** `/var/log/privacyidea/nginx.log`
- **Docker logs:** 
  - `docker-compose logs -f freeradius-privacyidea`
  - `docker-compose logs -f privacyidea`
  - `docker-compose logs -f freeradius-proxy`

## Troubleshooting

### Common Issues

1. **SSL Certificate Errors:**
   ```bash
   # Check certificate validity
   openssl s_client -connect your-privacyidea-server.com:443
   
   # Disable SSL validation temporarily
   export PRIVACYIDEA_VALIDATE_SSL=false
   ```

2. **Backend Connection Issues:**
   ```bash
   # Check backend connectivity
   telnet backend-server 1812
   
   # Verify secrets match
   radtest test test backend-server 0 secret
   ```

3. **Authentication Failures:**
   ```bash
   # Check FreeRADIUS logs
   tail -f /var/log/radius/radius.log
   
   # Test with debug mode
   radiusd -X -d /usr/local/etc/raddb
   ```

### Support

For Railway.com specific issues, check the Railway documentation or support channels. For FreeRADIUS configuration issues, consult the FreeRADIUS documentation.