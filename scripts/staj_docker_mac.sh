#!/usr/bin/env bash
# 1. haftanın Docker / Compose / Kubernetes denemelerini Docker Desktop'ta sırayla yeniden çalıştırır.
# Her adımdan sonra ekran görüntüsü alınabilsin diye bekler; devam etmek için Enter'a basın
# (ya da .staj_adim/devam_<n> dosyası oluşturulduğunda kendiliğinden geçer).
# Kullanım:  bash scripts/staj_docker_mac.sh
set -uo pipefail
cd "$(dirname "$0")/.."
ROOT=$PWD
FLAGS="$ROOT/.staj_adim"; mkdir -p "$FLAGS"; rm -f "$FLAGS"/devam_* 2>/dev/null
printf '\e[8;44;150t'          # Terminal penceresini 150x44 yap

G='\033[1;32m'; C='\033[1;36m'; D='\033[2m'; N='\033[0m'
baslik() { clear; printf "${C}▶ %s${N}\n\n" "$1"; }
run()    { printf "${G}\$ %s${N}\n" "$*"; eval "$@"; echo; }
bekle()  {
  printf "${D}── adım %s tamam · devam için Enter ──${N}" "$1"
  for _ in $(seq 1 900); do
    [ -f "$FLAGS/devam_$1" ] && { echo; return; }
    read -r -t 1 && return
  done; echo
}

# ------------------------------------------------------------------ hazırlık
baslik "Hazırlık: araç sürümleri"
run 'docker version --format "Docker Engine {{.Server.Version}} ({{.Server.Os}}/{{.Server.Arch}})"'
run 'docker compose version'
run 'kubectl version --client 2>/dev/null | head -1'
cd api && cp -n .env.example .env 2>/dev/null; cd "$ROOT"
run 'docker build -q -t mulakat-api:dev api'
bekle 0

# ------------------------------------------------------------------ gün 1
baslik "Gün 1 · Uygulama 127.0.0.1'i dinlerse konteyner dışından erişilemez"
docker rm -f api-127 api >/dev/null 2>&1
run 'docker run -d --name api-127 -p 8000:8000 mulakat-api:dev daphne -b 127.0.0.1 -p 8000 config.asgi:application'
sleep 4
run 'docker ps --filter name=api-127 --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"'
run 'curl -sS -m 5 http://localhost:8000/health/'
run "docker exec api-127 python -c 'import urllib.request as u; u.urlopen(\"http://127.0.0.1:8000/health/\")' 2>&1 | tail -n 1"
run 'docker logs api-127 2>&1 | grep -i listening'
bekle 1

baslik "Gün 1 · Bağlama adresi 0.0.0.0 olunca istek konteynere ulaşıyor"
docker rm -f api-127 >/dev/null 2>&1
run 'docker run -d --name api -p 8000:8000 mulakat-api:dev'
sleep 4
run 'docker logs api 2>&1 | grep -i listening'
run 'curl -sS -i http://localhost:8000/health/ | sed -n "1p;\$p"'
printf "${D}(503: ağ sorunu çözüldü, sıradaki eksik veritabanı bağlantısı)${N}\n\n"
docker rm -f api >/dev/null 2>&1
bekle 2

# ------------------------------------------------------------------ gün 2
cd "$ROOT/api"
baslik "Gün 2 · Compose içinde localhost, backend konteynerinin kendisidir"
run 'docker compose up -d --wait db'
run 'docker compose run --rm -e DB_HOST=localhost api python manage.py migrate 2>&1 | tail -n 4'
bekle 3

baslik "Gün 2 · Servis adı (db) ve healthcheck ile doğru bağlantı"
run 'docker compose up -d --build --wait 2>&1 | tail -n 4'
run 'docker compose ps --format "table {{.Service}}\t{{.Status}}\t{{.Ports}}"'
run 'docker compose exec -T api python manage.py migrate 2>&1 | tail -n 6'
run 'curl -sS http://localhost:8000/health/'
bekle 4

# ------------------------------------------------------------------ gün 3-4
baslik "Gün 3-4 · Sentetik transkript, migration durumu ve PostgreSQL üzerinde testler"
run 'docker compose exec -T api python manage.py seed_panel'
run 'docker compose exec -T api python manage.py showmigrations interviews'
run 'docker compose exec -T api python manage.py test 2>&1 | tail -n 4'
printf "Panel: http://localhost:8000/panel/1/\n\n"
bekle 5

# ------------------------------------------------------------------ gün 5
cd "$ROOT"
baslik "Gün 5 · Yalnız liveness probe: model yüklenmeden yeniden başlatma"
run 'kubectl config use-context docker-desktop >/dev/null && kubectl get nodes'
run 'docker build -q -t soru-servisi:1.0 k8s'
run 'kubectl apply -f k8s/deployment-liveness-only.yaml -f k8s/service.yaml'
printf "${D}(60 sn bekleniyor...)${N}\n"; sleep 60
run 'kubectl get pods -l app=soru-servisi'
run 'kubectl get events --field-selector reason=Unhealthy -o custom-columns=ZAMAN:.lastTimestamp,MESAJ:.message | tail -n 4'
run 'kubectl get events --field-selector reason=Killing -o custom-columns=ZAMAN:.lastTimestamp,MESAJ:.message | tail -n 2'
bekle 6

baslik "Gün 5 · startupProbe + readinessProbe ile yeni sürüm"
run 'kubectl apply -f k8s/deployment.yaml'
run 'kubectl rollout status deployment/soru-servisi --timeout=180s'
run 'kubectl get pods -l app=soru-servisi'
run 'kubectl get endpoints soru-servisi'
bekle 7

# ------------------------------------------------------------------ temizlik
baslik "Temizlik"
run 'kubectl delete -f k8s/deployment.yaml -f k8s/service.yaml --ignore-not-found'
cd "$ROOT/api" && run 'docker compose down -v'
rm -rf "$FLAGS"
printf "${G}Bitti.${N}\n"
