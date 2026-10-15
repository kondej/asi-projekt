# Architecture Decision Records

ADR dokumentuje jedną istotną decyzję architektoniczną: kontekst, rozważone opcje, wybór
i jego konsekwencje. W projekcie powstają dokładnie trzy ADR-y.

| ADR | Sprint | Temat |
|---|---|---|
| ADR-1 | S2 | Gdzie żyje przetwarzanie: input normalization, training-only filtering, model preprocessing |
| ADR-2 | S3 | Wybór modelu produkcyjnego i jego postać jako artefaktu |
| ADR-3 | S4 → S5 → S6 | Jak model trafia do usługi; stan i konfiguracja systemu; sekrety, cloud persistence i deployment |

ADR-3 powstaje stopniowo: szkic w Sprincie 4 (jak model trafia do usługi i obrazu),
uzupełnienie w Sprincie 5 (stan, persistence i konfiguracja w lokalnym systemie
wielousługowym), finalizacja w Sprincie 6 (sekrety, cloud persistence, deployment).

## Zasady

- Plik: `docs/adr/NNNN-krotki-tytul.md`, np. `docs/adr/0001-gdzie-zyje-przetwarzanie.md`.
  Szablon: [`template.md`](template.md).
- Autor i recenzent ADR to dwie różne osoby; obie są wpisane w dokumencie.
- ADR zawiera co najmniej dwie liczby z waszego systemu (np. metryki, czasy, rozmiary)
  i co najmniej jedną rozważoną, odrzuconą alternatywę z powodem odrzucenia.
- ADR trafia do repozytorium przez Pull Request jak każda inna zmiana.
- Zmiana decyzji to aktualizacja ADR (sekcja „Historia”) albo nowy ADR, który zastępuje stary.
