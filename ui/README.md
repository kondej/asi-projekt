# ui/ — interfejs użytkownika

> Scaffold for Sprint 5 — do not implement before this sprint.

W Sprincie 5 powstaje tu aplikacja Streamlit z własną listą zależności (obraz UI bez bibliotek ML).

Kontrakt:

- UI jest klientem API: formularz zgodny z kontraktem `/predict`, wynik i prawdopodobieństwo;
- adres API i token dostępu pochodzą ze zmiennych środowiskowych;
- UI nie importuje `asi_project` ani bibliotek ML;
- działanie UI potwierdza manualny UI check (Sprint 5); automatyczny smoke testuje tylko API.
