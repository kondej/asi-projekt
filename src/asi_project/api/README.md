# api/ — usługa predykcji

> Scaffold for Sprint 4 — do not implement before this sprint.

Pliki, które powstaną w Sprincie 4 (dokładny podział doprecyzuje zespół):

| Plik | Rola i kontrakt |
|---|---|
| aplikacja | `/healthz` (status, wersja modelu, tryb persistence) i `/predict` (etykieta, prawdopodobieństwo klasy pozytywnej, wersja modelu); model wczytywany raz; input normalization na wejściu |
| schematy | schemat Pydantic żądania i odpowiedzi — kontrakt projektuje zespół |
| ustawienia | konfiguracja z env (pydantic-settings z `env_file`) i prosty token dostępu do usługi `API_KEY` |
| repository | persistence z trybami `sql` i `disabled`; zapis rekordu predykcji |

Kolejne sprinty: S5 — ten sam kod z Postgresem w compose; S6 — `API_KEY` z Secret Managera
i jawny tryb `disabled` w Cloud Run bez zewnętrznej bazy. Testy API: `tests/api/`.
