#!/bin/sh

# 1. Create the cron job file
# This runs every hour. It finds files older than 24h (+1440 min) and deletes them.
cat <<EOF > /etc/cron.d/tuscleanup
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin
0 * * * * * root echo "Cron check: \$(date)" >> /var/log/cron.log 2>&1
0 * * * * root /usr/bin/find /app/data/uploads -type f -mmin +1440 -delete >> /var/log/cron.log 2>&1
EOF

# Le fichier dans cron.d doit avoir des permissions spécifiques
chmod 0644 /etc/cron.d/tuscleanup

# 2. Lancer le service cron
cron

# 3. Exécution de la commande passée au container (le CMD du Dockerfile)
# "$@" représente tous les arguments envoyés au script
exec "$@"