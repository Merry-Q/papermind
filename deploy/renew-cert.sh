#!/bin/sh
set -eu

docker run --rm --network host \
  -v /opt/1panel/apps/openresty/openresty/root:/webroot \
  -v /opt/1panel/apps/openresty/openresty/conf/conf.d/secure/letsencrypt:/etc/letsencrypt \
  certbot/certbot:latest renew --webroot -w /webroot --quiet
docker exec 1Panel-openresty-kN0y nginx -t
docker exec 1Panel-openresty-kN0y nginx -s reload
