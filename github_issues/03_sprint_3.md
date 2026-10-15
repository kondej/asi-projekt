# Sprint 3 — Eksperymenty, wybór modelu i artefakt

> Treść generowana z `docs/sprints/SPRINT_3.md` przez `python scripts/build_issues.py`. Zmiany wprowadzaj w pliku sprintu.

**Daty:** 12.11.2026 – 26.11.2026

## Cel

Zespół porównuje eksperymenty, wybiera model produkcyjny i zapisuje go jako pakiet,
który można wykorzystać bez ponownego treningu.

## Definition of Done

- [ ] Baseline jest zapisany jako run W&B.
- [ ] Runy W&B zawierają parametry, metryki, Git SHA i identyfikator wersji danych.
- [ ] AutoGluon działa jako część pipeline'u.
- [ ] Wykonano co najmniej dwie sensowne konfiguracje AutoGluona z limitem czasu.
- [ ] Przygotowano tabelę porównującą modele.
- [ ] Porównanie obejmuje główną metrykę, czas predykcji, rozmiar artefaktu i pamięć przy ładowaniu.
- [ ] Zespół wybrał model produkcyjny.
- [ ] Pakiet modelu zawiera model i `metadata.json`.
- [ ] Model jest zapisywany i wczytywany wspólnymi funkcjami.
- [ ] Pakiet modelu jest zapisany w W&B jako Artifact.
- [ ] Artefakt produkcyjny ma alias `production`.
- [ ] Smoke test pobiera `production`, wczytuje model i wykonuje predykcję.
- [ ] `docs/model_card.md` jest uzupełniony.
- [ ] ADR-2 jest napisany i zmergowany.
- [ ] CI na `main` jest zielone.
- [ ] Każda osoba w zespole ma własny obszar pracy i zrobiła merytoryczne review pracy innej osoby.

## Podział pracy (uzupełnia zespół na początku sprintu)

| Element sprintu | Owner | Recenzent |
| --- | --- | --- |
| _do uzupełnienia_ | | |

Integrator sprintu: _do uzupełnienia_

## Pełny opis

Plik `docs/sprints/SPRINT_3.md` w repozytorium.
