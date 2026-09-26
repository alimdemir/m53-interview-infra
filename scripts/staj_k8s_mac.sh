#!/usr/bin/env bash
# 5. günün Kubernetes adımları (Docker Desktop, kind):
#   1) Dockerfile düzeltildikten sonra aynı etiketle (1.0) derlenen imajın düğümde yenilenmemesi
#   2) yeni etiket (1.1) ile çözüm
#   3) yalnız liveness probe: model yüklenmeden yeniden başlatma
#   4) startupProbe + readinessProbe ile sorunsuz rollout
# Kullanım:  bash scripts/staj_k8s_mac.sh   (her adımdan sonra Enter ya da .staj_adim/devam_<n>)
set -uo pipefail
for d in /Applications/Docker.app/Contents/Resources/bin "$HOME/.docker/bin"; do
  [ -d "$d" ] && PATH="$d:$PATH"
done
export PATH
cd "$(dirname "$0")/.."
ROOT=$PWD
FLAGS="$ROOT/.staj_adim"; mkdir -p "$FLAGS"; rm -f "$FLAGS"/devam_* 2>/dev/null

G='\033[1;32m'; C='\033[1;36m'; D='\033[2m'; N='\033[0m'
baslik() { clear; printf "${C}▶ %s${N}\n\n" "$1"; }
run()    { printf "${G}\$ %s${N}\n" "$*"; eval "$@"; echo; }
bekle()  {
  printf "${D}── adım %s tamam · devam için Enter ──${N}" "$1"
  for _ in $(seq 1 1800); do
    [ -f "$FLAGS/devam_$1" ] && { echo; return; }
    read -r -t 1 && return
  done; echo
}
pod_bitsin() { kubectl wait --for=jsonpath='{.status.phase}'=Succeeded "pod/$1" --timeout=60s >/dev/null 2>&1; }

kubectl config use-context docker-desktop >/dev/null
# önceki denemeden kalanlar
kubectl delete deployment soru-servisi --ignore-not-found --wait=true >/dev/null 2>&1
kubectl delete pod kontrol-10 kontrol-11 --ignore-not-found --wait=true >/dev/null 2>&1
kubectl delete events --all >/dev/null 2>&1

baslik "Gün 5 · Dockerfile düzeldi, pod neden hâlâ eski dosyayı görüyor?"
run 'docker run --rm --entrypoint ls soru-servisi:1.0 -l /app/app.py'
run 'kubectl run kontrol-10 --image=soru-servisi:1.0 --image-pull-policy=IfNotPresent --restart=Never --command -- ls -l /app/app.py'
pod_bitsin kontrol-10
run 'kubectl logs kontrol-10'
run 'grep -n -A1 "image:" k8s/deployment.yaml'
bekle 1

baslik "Gün 5 · Çözüm: her değişiklikte yeni etiket"
run 'docker build -q -t soru-servisi:1.1 k8s'
run 'kubectl run kontrol-11 --image=soru-servisi:1.1 --image-pull-policy=IfNotPresent --restart=Never --command -- ls -l /app/app.py'
pod_bitsin kontrol-11
run 'kubectl logs kontrol-11'
kubectl delete pod kontrol-10 kontrol-11 --wait=false >/dev/null 2>&1
bekle 2

baslik "Gün 5 · Yalnız liveness probe: model yüklenmeden yeniden başlatma"
run 'kubectl apply -f k8s/deployment-liveness-only.yaml -f k8s/service.yaml'
printf "${D}(60 sn bekleniyor...)${N}\n"; sleep 60
run 'kubectl get pods -l app=soru-servisi'
run 'kubectl logs -l app=soru-servisi --previous --tail=2'
run 'kubectl get events --sort-by=.lastTimestamp --field-selector reason=Unhealthy -o custom-columns=NESNE:.involvedObject.name,MESAJ:.message | tail -n 3'
run 'kubectl get events --sort-by=.lastTimestamp --field-selector reason=Killing -o custom-columns=NESNE:.involvedObject.name,MESAJ:.message | tail -n 2'
bekle 3

baslik "Gün 5 · startupProbe + readinessProbe ile yeni sürüm"
run 'kubectl apply -f k8s/deployment.yaml'
printf "${D}(10 sn bekleniyor...)${N}\n"; sleep 10
run 'kubectl get pods -l app=soru-servisi'
run 'kubectl rollout status deployment/soru-servisi --timeout=180s'
run 'kubectl get pods -l app=soru-servisi'
run 'kubectl logs deployment/soru-servisi'
run 'kubectl get endpointslices -l kubernetes.io/service-name=soru-servisi -o custom-columns=ADRES:.endpoints[*].addresses[0],HAZIR:.endpoints[*].conditions.ready'
bekle 4

baslik "Temizlik"
run 'kubectl delete -f k8s/deployment.yaml -f k8s/service.yaml --ignore-not-found'
rm -rf "$FLAGS"
printf "${G}Bitti.${N}\n"
