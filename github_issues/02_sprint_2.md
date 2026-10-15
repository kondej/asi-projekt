# Sprint 2 — Reprodukowalny pipeline

> Treść generowana z `docs/sprints/SPRINT_2.md` przez `python scripts/build_issues.py`. Zmiany wprowadzaj w pliku sprintu.

**Daty:** 29.10.2026 – 12.11.2026

## Cel

Zespół przenosi proces treningowy z notebooka do Kedro, tak aby cały proces od danych
do modelu i metryk można było odtworzyć jedną komendą.

## Definition of Done

- [ ] Kedro działa w przypiętej wersji z `requirements/preflight-s2.txt`.
- [ ] Pipeline `data_processing` wykonuje walidację, input normalization i training-only filtering.
- [ ] Pipeline `data_science` wykonuje split, trening i ewaluację.
- [ ] Pipeline korzysta z logiki przygotowanej w Sprincie 1 zamiast ją duplikować.
- [ ] Model preprocessing nadal znajduje się wewnątrz sklearn `Pipeline`.
- [ ] Parametry są przeniesione do konfiguracji.
- [ ] Data Catalog opisuje wejścia i wyjścia pipeline'u.
- [ ] `conf/ci/` pozwala uruchomić pipeline na próbce CI.
- [ ] Testy nodów przechodzą.
- [ ] `kedro run` na pełnych danych tworzy model i metryki.
- [ ] `kedro run --env ci` działa w CI.
- [ ] Notebook nie jest już wymagany do trenowania baseline'u.
- [ ] ADR-1 jest napisany i zmergowany.
- [ ] README zawiera sekcję „Kedro quickstart”.
- [ ] CI na `main` jest zielone.
- [ ] Każda osoba w zespole ma własny obszar pracy i zrobiła merytoryczne review pracy innej osoby.

## Podział pracy (uzupełnia zespół na początku sprintu)

| Element sprintu | Owner | Recenzent |
| --- | --- | --- |
| _do uzupełnienia_ | | |

Integrator sprintu: _do uzupełnienia_

## Pełny opis

Plik `docs/sprints/SPRINT_2.md` w repozytorium.
