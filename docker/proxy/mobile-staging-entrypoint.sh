#!/bin/sh
# Entrypoint of the mobile staging proxy.
# Always serves plain HTTP (default.conf). If MOBILE_DOMAIN is set and its
# Let's Encrypt certificate exists, it also serves HTTPS on container port 443.
set -eu

CERT="/etc/letsencrypt/live/${MOBILE_DOMAIN:-}/fullchain.pem"

if [ -n "${MOBILE_DOMAIN:-}" ] && [ -f "$CERT" ]; then
  echo "Certificate found for ${MOBILE_DOMAIN}: enabling HTTPS"
  sed "s/__DOMAIN__/${MOBILE_DOMAIN}/g" \
    /etc/nginx/mobile-staging-tls.conf.tpl > /etc/nginx/conf.d/tls.conf
else
  echo "No certificate for '${MOBILE_DOMAIN:-}': HTTP only"
fi

exec nginx -g 'daemon off;'
