#!/usr/bin/env bash
code() { curl -s -o /dev/null -m 3 -w "%{http_code}" "$1"; }
echo "receiver /status : $(code localhost:8080/status)"
echo "pythia   /stats  : $(code localhost:8011/stats)"
echo "storage  /status : $(docker exec storage curl -s -o /dev/null -m 3 -w '%{http_code}' localhost:8090/status 2>/dev/null || echo down)"
docker exec db mysql -u walkr_user -pwalkr_passwd walkr_db -N \
  -e "SELECT 'distance', COUNT(*) FROM distance UNION ALL SELECT 'steps', COUNT(*) FROM steps;" 2>/dev/null || echo "mysql: down"
docker ps --format "table {{.Names}}\t{{.Status}}"