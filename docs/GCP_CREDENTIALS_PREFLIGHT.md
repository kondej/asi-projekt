# Pre-flight GCP na student credentials (checklista prowadzącej)

Status: **NIEWYKONANY** — student credentials nie zostały jeszcze przekazane.
Kolumnę „Wynik” uzupełniamy dopiero po faktycznym sprawdzeniu. Nie wpisujemy wyników
przewidywanych ani zakładanych.

## Cel

Sprawdzić, czy na uprawnieniach student credentials da się wykonać wszystko, czego wymagają
Sprinty 4–6: Artifact Registry, Cloud Run, Secret Manager, Cloud Logging. Wynik musi być znany
**przed pre-flightem GCP zespołów w Sprincie 4** (start sprintu 26.11.2026).

Jeżeli któraś usługa wymagana w CORE okaże się niedostępna, jest to konkretny błąd planu —
decyzja o zamienniku zapada przed Sprintem 4.

## Przebieg

Test wykonujemy na koncie z takimi samymi uprawnieniami jak konta studentów, w nowym projekcie
testowym, w regionie wybranym dla kursu. Polecenia są przykładowe — zapisujemy faktycznie
użyte warianty.

| # | Sprawdzenie | Przykładowe polecenie / sposób | Oczekiwany wynik | Wynik (do uzupełnienia) | Uwagi |
|---|---|---|---|---|---|
| 1 | Logowanie i konfiguracja CLI | `gcloud auth login`, `gcloud config list` | konto aktywne | | |
| 2 | Utworzenie projektu | konsola albo `gcloud projects create <id>` | projekt istnieje | | |
| 3 | Billing / kredyty | konsola Billing: konto rozliczeniowe przypięte do projektu | kredyty widoczne | | |
| 4 | Włączenie API | `gcloud services enable run.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com logging.googleapis.com` | API włączone | | |
| 5 | Uprawnienia IAM w projekcie | `gcloud projects get-iam-policy <id>` | znana lista ról studenta | | |
| 6 | Dodanie prowadzącej jako Viewer (warunkowe, nie jest DoD) | `gcloud projects add-iam-policy-binding <id> --member=user:<email> --role=roles/viewer` | operacja dozwolona albo nie | | brak uprawnień nie wpływa na zaliczenie |
| 7 | Repozytorium Artifact Registry | `gcloud artifacts repositories create <repo> --repository-format=docker --location=<region>` | repozytorium istnieje | | |
| 8 | Push obrazu `linux/amd64` | `gcloud auth configure-docker <region>-docker.pkg.dev`, `docker buildx build --platform=linux/amd64 ... --push` | obraz w rejestrze | | |
| 9 | Publiczny deploy Cloud Run | `gcloud run deploy hello --image=us-docker.pkg.dev/cloudrun/container/hello --region=<region> --allow-unauthenticated` | URL odpowiada | | polityki organizacji mogą blokować dostęp publiczny |
| 10 | Ustawienia usługi | `--memory`, `--timeout`, `--min-instances=0`, `--session-affinity` | ustawienia przyjęte | | wymagane dla UI w Streamlit |
| 11 | Sekret w Secret Manager | `gcloud secrets create asi-api-key --data-file=-` | sekret istnieje | | |
| 12 | Dostęp usługi do sekretu | nadanie roli Secret Manager Secret Accessor kontu usługi Cloud Run i deploy z `--set-secrets=API_KEY=asi-api-key:1` | usługa widzi wartość jako zmienną środowiskową | | |
| 13 | Odczyt logów | `gcloud logging read 'resource.type="cloud_run_revision"' --limit=10` | logi usługi widoczne | | |
| 14 | Kontrola kosztów | konsola Billing: budżet i alert | budżet ustawiony albo informacja o braku uprawnień | | |
| 15 | Sprzątanie | usunięcie usługi, obrazów, sekretu i projektu testowego | brak zasobów | | |

## Decyzje po pre-flighcie

| Obszar | Wynik | Konsekwencja dla Sprintów 4–6 |
|---|---|---|
| Artifact Registry | | |
| Cloud Run (w tym dostęp publiczny) | | |
| Secret Manager | | |
| Cloud Logging | | |
| IAM / Viewer dla prowadzącej | | wyłącznie warunkowo; nie jest DoD |
| Billing / kredyty | | |

Data wykonania: — · Wykonała: —
