FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

RUN apt-get update && apt-get install -y --no-install-recommends \
    freeradius \
    freeradius-python3 \
    freeradius-rest \
    python3 \
    python3-pip \
    python3-requests \
    nginx \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /app/data /etc/freeradius/3.0 && \
    chown -R freerad:freerad /app/data

COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

RUN echo 'server { listen 80; location / { return 200 "FreeRADIUS is running\n"; add_header Content-Type text/plain; } }' > /etc/nginx/sites-available/default

EXPOSE 80 1812/udp 1813/udp

WORKDIR /etc/freeradius/3.0

ENTRYPOINT ["/docker-entrypoint.sh"]
