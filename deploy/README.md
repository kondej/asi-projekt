# deploy/ — wdrożenie w Google Cloud

> Scaffold for Sprint 6 — do not implement before this sprint.

W Sprincie 6 powstaje tu `deploy.sh` (jego szkielet zespoły dostają na starcie sprintu).

Checklista ograniczeń platformy (Cloud Run):

- port z `$PORT`;
- architektura obrazu `linux/amd64`;
- pamięć dobrana testem `--memory`;
- min instances i cold start;
- dla Streamlita dodatkowo: WebSocket, request timeout rzędu minut, session affinity,
  jeśli jest potrzebna.

Kontrakt wdrożenia (z planu Sprintu 6):

- `API_KEY` jest przechowywany w Secret Managerze; obie usługi otrzymują go przez integrację
  z Secret Managerem; reszta konfiguracji przez zmienne środowiskowe;
- bez zewnętrznej bazy tryb persistence `disabled` jest ustawiony jawnie, a `/healthz`
  go raportuje;
- ten sam skrypt smoke co od Sprintu 4 działa na adresach URL usług (14.01 i 21.01);
- release v1.0 z notatkami: adresy URL, wersja modelu, run W&B, tag obrazu.

Wykonalność usług na student credentials: `docs/GCP_CREDENTIALS_PREFLIGHT.md`.
