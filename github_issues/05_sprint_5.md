# Sprint 5 — System lokalny: UI, API i Postgres

> Treść generowana z `docs/sprints/SPRINT_5.md` przez `python scripts/build_issues.py`. Zmiany wprowadzaj w pliku sprintu.

**Daty:** 17.12.2026 – 07.01.2027

## Cel

Zespół łączy Streamlit, FastAPI i PostgreSQL w lokalny system uruchamiany jedną komendą
przez Docker Compose.

## Definition of Done

- [ ] Streamlit zawiera formularz zgodny z kontraktem API.
- [ ] UI pokazuje etykietę i prawdopodobieństwo klasy pozytywnej.
- [ ] Adres API jest pobierany z env.
- [ ] `API_KEY` jest pobierany z env.
- [ ] Dockerfile UI działa.
- [ ] Obraz UI nie zawiera niepotrzebnych zależności ML.
- [ ] `docker-compose.yml` uruchamia `api`, `ui` i `db`.
- [ ] `db` działa na PostgreSQL.
- [ ] PostgreSQL korzysta z nazwanego wolumenu.
- [ ] API ma sterownik PostgreSQL.
- [ ] API korzysta z PostgreSQL przez istniejącą warstwę repository.
- [ ] Hasła i tokeny nie są wpisane bezpośrednio do Compose.
- [ ] `.env.example` jest uzupełniony.
- [ ] Healthchecki są skonfigurowane.
- [ ] `docker compose up --build` uruchamia cały system.
- [ ] Automatyczny smoke przechodzi w trybie `sql`.
- [ ] Rekord predykcji jest zapisany w PostgreSQL.
- [ ] Manualny UI check został wykonany.
- [ ] README zawiera „Docker quickstart”.
- [ ] ADR-3 jest uzupełniony.
- [ ] W repozytorium nie ma sekretów.
- [ ] CI na `main` jest zielone.
- [ ] Każda osoba w zespole ma własny obszar pracy i zrobiła merytoryczne review pracy innej osoby.

## Podział pracy (uzupełnia zespół na początku sprintu)

| Element sprintu | Owner | Recenzent |
| --- | --- | --- |
| _do uzupełnienia_ | | |

Integrator sprintu: _do uzupełnienia_

## Pełny opis

Plik `docs/sprints/SPRINT_5.md` w repozytorium.
