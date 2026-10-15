# Sprint 6 — Wdrożenie do Cloud Run, obserwowalność i release

> Treść generowana z `docs/sprints/SPRINT_6.md` przez `python scripts/build_issues.py`. Zmiany wprowadzaj w pliku sprintu.

**Daty:** 07.01.2027 – 21.01.2027

## Cel

Zespół wdraża API i UI do Cloud Run, konfiguruje sekrety i logi oraz przygotowuje
finalny release `v1.0`.

## Definition of Done

- [ ] API jest wdrożone do Cloud Run.
- [ ] UI jest wdrożone do Cloud Run.
- [ ] Obrazy są zgodne z `linux/amd64`.
- [ ] API korzysta z `$PORT`.
- [ ] `API_KEY` znajduje się w Secret Managerze.
- [ ] API otrzymuje `API_KEY` przez integrację z Secret Managerem.
- [ ] UI otrzymuje `API_KEY` przez integrację z Secret Managerem.
- [ ] Persistence w chmurze jest ustawione jawnie.
- [ ] Przy braku zewnętrznej bazy działa `persistence = disabled`.
- [ ] SQLite w Cloud Run jest zablokowany.
- [ ] `/healthz` działa.
- [ ] Smoke test na publicznym URL API przechodzi.
- [ ] Manualny UI check przechodzi.
- [ ] Logi predykcji są widoczne w Cloud Logging.
- [ ] Finalny smoke test przechodzi.
- [ ] Finalny manualny UI check przechodzi.
- [ ] README jest aktualne.
- [ ] Model Card jest aktualna.
- [ ] ADR-3 jest finalny.
- [ ] `deploy.sh` odpowiada rzeczywistemu deploymentowi.
- [ ] W repozytorium nie ma sekretów.
- [ ] Release notes są przygotowane.
- [ ] Release `v1.0` jest utworzony.
- [ ] Zespół jest gotowy do demo.

## Podział pracy (uzupełnia zespół na początku sprintu)

| Element sprintu | Owner | Recenzent |
| --- | --- | --- |
| _do uzupełnienia_ | | |

Integrator sprintu: _do uzupełnienia_

## Pełny opis

Plik `docs/sprints/SPRINT_6.md` w repozytorium.
