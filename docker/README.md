# docker/ — obrazy kontenerów

> Scaffold for Sprint 4 and Sprint 5 — do not implement before these sprints.

| Plik | Sprint | Kontrakt |
|---|---|---|
| `docker/api.Dockerfile` | S4 | obraz API bez condy; wersje bibliotek modelu jak w treningu; port z `$PORT`; bez sekretów i adresów w obrazie |
| `.dockerignore` (katalog główny) | S4 | do obrazu nie trafiają dane, sekrety ani lokalne artefakty |
| `.env.example` (katalog główny) | S4, uzupełniany w S5 | nazwy zmiennych bez prawdziwych wartości |
| `docker/ui.Dockerfile` | S5 | obraz UI bez zależności ML |
| `docker-compose.yml` (katalog główny) | S5 | usługi `api`, `ui` i `db` (Postgres z nazwanym wolumenem), konfiguracja z `.env`, healthchecki |

Na potrzeby Cloud Run obraz API budujemy jako `linux/amd64` (pre-flight w S5, wdrożenie w S6).
