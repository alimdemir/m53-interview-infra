# M53 Mülakat Altyapısı · Docker, Compose ve Kubernetes

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.2-092E20?logo=django)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Kubernetes](https://img.shields.io/badge/Kubernetes-probes-326CE5?logo=kubernetes&logoColor=white)
[![CI](https://github.com/alimdemir/m53-interview-infra/actions/workflows/ci.yml/badge.svg)](https://github.com/alimdemir/m53-interview-infra/actions/workflows/ci.yml)

Bu repo, [M53 multimodal mülakat sisteminin](https://github.com/alimdemir/m53-multimodal-interview) backend servisini konteynerleştirme, PostgreSQL ile birlikte çalıştırma ve model servislerini Kubernetes'te sağlık kontrolleriyle yayınlama üzerine yaptığım çalışmaları içeriyor. AVD Teknoloji Danışmanlık'taki stajımın (2026) ilk haftasında hazırladım. Her adımda karşılaştığım hatalar ve çözümleri aşağıda.

## İçerik

| Klasör | Açıklama |
|---|---|
| [`api/`](api) | Django 5.2 + Channels API. Mülakat, transkript parçası ve soru önerisi modelleri, `/health/` ucu, WebSocket transkript paneli, `Dockerfile`, `compose.yaml` (PostgreSQL 16 + healthcheck) |
| [`k8s/`](k8s) | Modeli yüklerken geç hazır olan örnek servis; startup/readiness/liveness probe'lu `Deployment` ve `Service` |
| [`scripts/`](scripts) | macOS'ta Docker Desktop ile adım adım deneme betikleri (`staj_docker_mac.sh`: Compose ve temel probe senaryosu, `staj_k8s_mac.sh`: imaj izni, etiket ve probe karşılaştırması) |
| [`docs/ekran_goruntuleri/`](docs/ekran_goruntuleri) | Çalışma sırasında aldığım ekran görüntüleri |

## Mimari

```mermaid
flowchart LR
    P["Tarayıcı paneli"] -- "HTTP / WebSocket" --> A["api<br/>Daphne (ASGI)<br/>Django + Channels"]
    A -- "psycopg" --> D[("db<br/>PostgreSQL 16")]
    D -. "pg_isready healthcheck" .-> A
```

- **HTTP**: kayıt oluşturma, sorgulama ve `/health/` (veritabanına `SELECT 1` atar, ulaşamazsa `503` döner)
- **WebSocket** (`/ws/interviews/<id>/`): panel açıldığında transkript parçaları sırayla JSON olarak akar
- **Şema**: `Interview 1─N TranscriptSegment`, `QuestionSuggestion → TranscriptSegment (SET_NULL)`, `(interview, start_ms)` indeksi

## Hızlı başlangıç

```bash
cd api
cp .env.example .env                 # parolaları değiştirin; .env repoya girmez
docker compose up -d --build --wait
docker compose exec api python manage.py migrate
curl http://localhost:8000/health/
# {"service": "mulakat-api", "db": "ok"}
```

Deneme verisi için `docker compose exec api python manage.py createsuperuser` ile `/admin/` paneline girip bir mülakat ve transkript parçaları ekleyin. Ardından `http://localhost:8000/panel/<id>/` sayfasını açın.

Docker olmadan hızlı test (SQLite):

```bash
cd api && python -m venv .venv && .venv/bin/pip install -r requirements.txt
DB_ENGINE=sqlite .venv/bin/python manage.py test -v 2
```

## Kubernetes: model servisi ve probe'lar

`k8s/app.py`, açılışta modeli belleğe yüklüyormuş gibi yaklaşık 25 saniye bekleyen bir servis. Yükleme bitene kadar `/healthz` ve `/ready` uçları `503` döner.

```bash
docker build -t soru-servisi:1.1 k8s/
# Docker Desktop'ın yerleşik kümesi yerel imajı doğrudan görür.
# Ayrı bir kind kümesinde:  kind load docker-image soru-servisi:1.1
# minikube:                 minikube image load soru-servisi:1.1
kubectl apply -f k8s/deployment.yaml -f k8s/service.yaml
kubectl rollout status deployment/soru-servisi
```

Karşılaştırma için `k8s/deployment-liveness-only.yaml` yalnızca liveness probe içeren ilk sürümü tutuyor. İmaj her değiştiğinde etiketi de değiştiriyorum (`1.0` → `1.1`); sebebi aşağıdaki tabloda.

| Probe | Görevi | Ayar |
|---|---|---|
| `startupProbe` | Yükleme için süre tanır; bitene kadar diğer probe'lar çalışmaz | 12 × 5 sn = 60 sn |
| `readinessProbe` | Pod hazır değilken Service trafiği göndermez | 5 sn aralık |
| `livenessProbe` | Kilitlenen konteyneri yeniden başlatır | 3 hata × 10 sn |

## Karşılaştığım sorunlar ve çözümleri

| Belirti | Neden | Çözüm |
|---|---|---|
| `curl: Connection reset by peer`, konteynerin içinden istek çalışıyor | Sunucu yalnızca `127.0.0.1` adresini dinliyordu | Bağlama adresini `0.0.0.0:8000` yaptım |
| `migrate` → `Connection refused` | Compose içinde `localhost`, backend konteynerinin kendisini gösteriyor | `DB_HOST=db` (servis adı) |
| API veritabanından önce açılıyor | `depends_on` yalnızca başlatma sırasını belirliyor | `pg_isready` healthcheck + `condition: service_healthy` |
| `column ... does not exist` | Model değişti ama migration uygulanmadı | `makemigrations` → `showmigrations` → `migrate` |
| WebSocket loglarında `ı` gibi kaçışlar | `json.dumps` varsayılanı `ensure_ascii=True` | Consumer'da `ensure_ascii=False` |
| Pod açılır açılmaz `Error`: `can't open file '/app/app.py': [Errno 13] Permission denied` | Mac'teki dosyanın izni `0600` idi; `COPY` izni imaja aynen taşıdı, uygulama ise root olmayan kullanıcıyla (uid 10001) çalışıyor | `COPY --chmod=0644 app.py .` |
| Dockerfile düzeldiği hâlde pod'lar aynı hatayı veriyor | İmaj aynı `1.0` etiketiyle yeniden derlendi; `imagePullPolicy: IfNotPresent` olduğu için düğüm önbellekteki eski imajı kullandı | Her değişiklikte yeni etiket (`1.1`); `latest` gibi değişen etiketlere güvenmemek |
| Pod model yüklenmeden yeniden başlatılıyor | Yalnızca liveness probe vardı; model yüklenirken `/healthz` 503 dönüyor | `startupProbe` + ayrı `readinessProbe` + kaynak sınırları |
| Liveness hatasından sonra konteyner ~30 sn geç kapanıyor (önceki logda `model hazır` görünüyor) | Python konteynerde PID 1; işleyicisi olmayan `SIGTERM` iletilmiyor, kubelet 30 sn'lik `terminationGracePeriodSeconds` sonunda `SIGKILL` gönderiyor | Açık not: `SIGTERM` işleyicisi eklemek ya da tini gibi bir init süreci kullanmak |

## Testler

`api/interviews/tests.py` altında 7 test var: sağlık ucu, transkript sıralaması, silme davranışları (`CASCADE` / `SET_NULL`), panel görünümü ve WebSocket akışı (`channels.testing.WebsocketCommunicator`).

GitHub Actions iş akışı ([`ci.yml`](.github/workflows/ci.yml)) her push'ta iki iş çalıştırıyor: Compose ile API + PostgreSQL'i kaldırıp migration, `/health/` kontrolü ve testler; ayrı bir kind kümesinde `soru-servisi` imajını yükleyip startupProbe'lu Deployment'ın rollout'unu bekleme.

## Ekran görüntüleri

Görüntüleri MacBook Air (Apple Silicon) üzerinde Docker Desktop ve yerleşik Kubernetes (kind) kümesiyle, `scripts/` altındaki betikleri çalıştırırken aldım.

| | |
|---|---|
| ![](docs/ekran_goruntuleri/01_baglama_adresi_hata.jpg)<br/>Uygulama `127.0.0.1` dinlediği için dışarıdan erişilemiyor | ![](docs/ekran_goruntuleri/02_baglama_adresi_cozum.jpg)<br/>`0.0.0.0` sonrası erişim |
| ![](docs/ekran_goruntuleri/03_compose_localhost_hatasi.jpg)<br/>`DB_HOST=localhost` ile bağlantı hatası | ![](docs/ekran_goruntuleri/04_compose_servis_adi_cozum.jpg)<br/>Servis adı + healthcheck, migration ve `/health/` |
| ![](docs/ekran_goruntuleri/05_websocket_transkript_paneli.jpg)<br/>WebSocket transkript paneli | ![](docs/ekran_goruntuleri/06_seed_migration_test.jpg)<br/>Deneme verisi, migration durumu ve PostgreSQL üzerinde testler |
| ![](docs/ekran_goruntuleri/07_k8s_izin_hatasi.jpg)<br/>`0600` dosya izni imaja taşındı: `Permission denied` | ![](docs/ekran_goruntuleri/08_k8s_ayni_etiket_eski_imaj.jpg)<br/>Aynı etiket: yerel imaj düzeldi, düğümdeki imaj eski |
| ![](docs/ekran_goruntuleri/09_k8s_liveness_yeniden_baslatma.jpg)<br/>Yalnız liveness probe: model yüklenirken yeniden başlatma | ![](docs/ekran_goruntuleri/10_k8s_startup_probe_cozum.jpg)<br/>startupProbe + readinessProbe ile rollout; EndpointSlice'ta yalnız yeni pod hazır |

## Lisans

[MIT](LICENSE)
