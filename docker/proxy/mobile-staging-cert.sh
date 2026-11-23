#!/bin/sh
# Issue or renew the Let's Encrypt certificate of the mobile staging stack.
#
# Run from anywhere on the server, with sudo (it needs the Docker socket):
#   sudo sh docker/proxy/mobile-staging-cert.sh dry-run   # test, issues nothing
#   sudo sh docker/proxy/mobile-staging-cert.sh issue     # first real certificate
#   sudo sh docker/proxy/mobile-staging-cert.sh renew     # renew if due (cron)
#
# How it works: Let's Encrypt requests
#   http://<MOBILE_DOMAIN>/.well-known/acme-challenge/<token>
# on port 80. Port 80 of this server belongs to the existing staging proxy,
# which serves /vol/www from the Docker volume WEBROOT_VOLUME. certbot writes
# the token file into that volume (and removes it afterwards); nothing else in
# that volume is touched. The certificate itself is stored in this stack's own
# volume CERTS_VOLUME, which the mobile proxy mounts.
#
# Reads MOBILE_DOMAIN and ACME_EMAIL from the .env file in the repo root.
set -eu

WEBROOT_VOLUME="${WEBROOT_VOLUME:-gesis_surf_backend_certbot-web}"
CERTS_VOLUME="${CERTS_VOLUME:-gesis_mobile_staging_certbot-certs}"
COMPOSE_FILE="docker-compose.mobile-staging.yaml"

cd "$(dirname "$0")/../.."

get_env() {
  grep -E "^$1=" .env | head -n 1 | cut -d= -f2-
}

DOMAIN="$(get_env MOBILE_DOMAIN)"
EMAIL="$(get_env ACME_EMAIL)"
[ -n "$DOMAIN" ] || { echo "MOBILE_DOMAIN is not set in .env" >&2; exit 1; }

certbot_run() {
  docker run --rm \
    -v "$WEBROOT_VOLUME":/vol/www \
    -v "$CERTS_VOLUME":/etc/letsencrypt \
    certbot/certbot "$@"
}

need_email() {
  [ -n "$EMAIL" ] || { echo "ACME_EMAIL is not set in .env" >&2; exit 1; }
}

case "${1:-}" in
  dry-run)
    need_email
    certbot_run certonly --webroot -w /vol/www -d "$DOMAIN" \
      --email "$EMAIL" --agree-tos --no-eff-email --non-interactive --dry-run
    ;;
  issue)
    need_email
    certbot_run certonly --webroot -w /vol/www -d "$DOMAIN" \
      --email "$EMAIL" --agree-tos --no-eff-email --non-interactive
    echo "Certificate issued. Restart the proxy so it enables HTTPS:"
    echo "  docker compose -f $COMPOSE_FILE restart proxy"
    ;;
  renew)
    certbot_run renew --webroot -w /vol/www --non-interactive
    docker compose -f "$COMPOSE_FILE" exec -T proxy nginx -s reload
    ;;
  *)
    echo "Usage: $0 dry-run | issue | renew" >&2
    exit 1
    ;;
esac
