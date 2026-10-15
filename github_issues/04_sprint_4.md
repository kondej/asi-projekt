# Sprint 4 — API, persistence i pierwszy kontener

> Treść generowana z `docs/sprints/SPRINT_4.md` przez `python scripts/build_issues.py`. Zmiany wprowadzaj w pliku sprintu.

**Daty:** 26.11.2026 – 17.12.2026

## Cel

Zespół udostępnia model przez FastAPI, dodaje walidację, persistence i prosty token dostępu,
a następnie uruchamia usługę w kontenerze.

## Definition of Done

- [ ] `/healthz` działa i zwraca status, wersję modelu i tryb persistence.
- [ ] `/predict` ma schemat Pydantic zgodny z kontraktem modelu.
- [ ] `/predict` zwraca etykietę, prawdopodobieństwo klasy pozytywnej i wersję modelu.
- [ ] Model jest ładowany raz przy starcie aplikacji.
- [ ] API wykonuje input normalization przed modelem.
- [ ] Model preprocessing pozostaje wewnątrz zapisanego modelu.
- [ ] Konfiguracja działa przez `pydantic-settings`.
- [ ] `.env.example` znajduje się w repozytorium i nie zawiera sekretów.
- [ ] `/predict` wymaga poprawnego `API_KEY`.
- [ ] Brak lub zły token zwraca 401.
- [ ] `/healthz` nie wymaga tokenu.
- [ ] Repository obsługuje tryby `sql` i `disabled`.
- [ ] SQLite działa przez SQLAlchemy.
- [ ] Predykcje są zapisywane w trybie `sql`.
- [ ] Każda predykcja generuje log JSON.
- [ ] Testy API przechodzą.
- [ ] Dockerfile API działa lokalnie.
- [ ] Port usługi jest pobierany z `$PORT`.
- [ ] SQLite jest podłączone przez wolumen.
- [ ] Kontener został sprawdzony z limitem pamięci.
- [ ] Wspólny smoke test API przechodzi.
- [ ] Szkic ADR-3 jest zmergowany.
- [ ] W repozytorium nie ma sekretów.
- [ ] CI na `main` jest zielone.
- [ ] Każda osoba w zespole ma własny obszar pracy i zrobiła merytoryczne review pracy innej osoby.

## Podział pracy (uzupełnia zespół na początku sprintu)

| Element sprintu | Owner | Recenzent |
| --- | --- | --- |
| _do uzupełnienia_ | | |

Integrator sprintu: _do uzupełnienia_

## Pełny opis

Plik `docs/sprints/SPRINT_4.md` w repozytorium.
