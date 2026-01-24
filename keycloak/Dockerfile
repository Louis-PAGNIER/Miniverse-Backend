FROM quay.io/keycloak/keycloak:26.5.0 AS builder

# Enable health and metrics support
ENV KC_HEALTH_ENABLED=true
ENV KC_METRICS_ENABLED=true

# Configure a database vendor
ENV KC_DB=mysql

# Condigure proxy mode
ENV KC_HTTP_ENABLED=true
ENV KC_HOSTNAME_STRICT=false
ENV KC_PROXY_HEADERS=forwarded
ENV KC_HTTP_RELATIVE_PATH=/keycloak

WORKDIR /opt/keycloak
RUN /opt/keycloak/bin/kc.sh build

FROM quay.io/keycloak/keycloak:26.5.0
COPY --from=builder /opt/keycloak/ /opt/keycloak/

# change these values to point to a running postgres instance
ENV KC_DB=mysql
ENV KC_DB_URL=jdbc:mysql://mysql/keycloak_db
ENV KC_DB_USERNAME=keycloak_db_user

ENV KC_HTTP_ENABLED=true
ENV KC_HOSTNAME_STRICT=false
ENV KC_PROXY_HEADERS=forwarded
ENV KC_HTTP_RELATIVE_PATH=/keycloak

COPY import/ /opt/keycloak/data/import/

ENTRYPOINT ["/opt/keycloak/bin/kc.sh"]