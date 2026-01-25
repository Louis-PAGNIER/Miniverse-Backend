#!/bin/sh

# On arrête le script en cas d'erreur
set -e

# Nom de domaine et dossier où stocker les certs
DOMAIN=${DOMAIN_NAME:-localhost}
SSL_DIR="/etc/nginx/ssl"
mkdir -p $SSL_DIR

# Génération seulement si les fichiers n'existent pas
if [ ! -f "$SSL_DIR/server.key" ] || [ ! -f "$SSL_DIR/server.crt" ]; then

    echo "🔐 Génération du certificat pour : $DOMAIN"
    openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
        -keyout "$SSL_DIR/server.key" \
        -out "$SSL_DIR/server.crt" \
        -subj "/C=FR/O=Miniverse/CN=$DOMAIN" \
        -quiet
fi

# On lance la commande passée en argument au Docker (ici: nginx -g 'daemon off;')
exec "$@"