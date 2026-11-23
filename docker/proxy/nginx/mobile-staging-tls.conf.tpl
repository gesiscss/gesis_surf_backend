# HTTPS server block for the mobile staging stack.
# Only enabled by mobile-staging-entrypoint.sh once the certificate exists.
# __DOMAIN__ is replaced with MOBILE_DOMAIN at container start.

server {
    listen 443 ssl;
    server_name __DOMAIN__;

    ssl_certificate     /etc/letsencrypt/live/__DOMAIN__/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/__DOMAIN__/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers "ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305";
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:mobile_tls:10m;
    ssl_session_timeout 1h;
    ssl_session_tickets off;

    send_timeout 300s;

    location /static {
        alias /vol/static;
    }

    location / {
        uwsgi_pass           app:9000;
        include              /etc/nginx/uwsgi_params;
        uwsgi_param          HTTP_HOST $http_host;
        uwsgi_param          HTTP_X_FORWARDED_PROTO https;
        client_max_body_size 20M;
    }
}
