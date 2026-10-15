"""Generuje treść GitHub Issues (github_issues/) z plików sprintów (docs/sprints/).

Jedno źródło prawdy: docs/sprints/SPRINT_N.md. Pliki w github_issues/ są generowane —
zmiany wprowadzamy w pliku sprintu i uruchamiamy ponownie skrypt.

Użycie:
    python scripts/build_issues.py           # zapisuje github_issues/0N_sprint_N.md
    python scripts/build_issues.py --check   # kod 1, jeśli pliki są nieaktualne (test w CI)

Utworzenie issue (GitHub CLI):
    gh issue create --title "Sprint 1 — ..." --body-file github_issues/01_sprint_1.md
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPRINTS = range(1, 7)


def section(lines: list[str], heading: str) -> list[str]:
    """Linie sekcji ``## heading`` (bez nagłówka) do następnego nagłówka ``## ``."""
    try:
        start = lines.index(f"## {heading}") + 1
    except ValueError as error:
        raise ValueError(f"Brak sekcji '## {heading}'") from error
    end = next((i for i in range(start, len(lines)) if lines[i].startswith("## ")), len(lines))
    return lines[start:end]


def bullet_items(lines: list[str]) -> list[str]:
    """Punkty listy, również zapisane jako Markdown checklist."""
    items: list[str] = []

    for line in lines:
        if line.startswith("- [ ] "):
            items.append(line[6:].strip())
        elif line.startswith("- [x] ") or line.startswith("- [X] "):
            items.append(line[6:].strip())
        elif line.startswith("- "):
            items.append(line[2:].strip())
        elif line.startswith("  ") and line.strip() and items:
            items[-1] = f"{items[-1]} {line.strip()}"

    return items


def render_issue(number: int, sprint_text: str) -> str:
    lines = sprint_text.splitlines()
    title = lines[0].removeprefix("# ").strip()
    dates = next(line for line in lines if line.startswith("**Daty:**"))
    goal = [line for line in section(lines, "Cel") if line.strip()]
    dod = bullet_items(section(lines, "Definition of Done"))
    checklist = [f"- [ ] {item}" for item in dod]
    body = [
        f"# {title}",
        "",
        f"> Treść generowana z `docs/sprints/SPRINT_{number}.md` przez "
        "`python scripts/build_issues.py`. Zmiany wprowadzaj w pliku sprintu.",
        "",
        dates,
        "",
        "## Cel",
        "",
        *goal,
        "",
        "## Definition of Done",
        "",
        *checklist,
        "",
        "## Podział pracy (uzupełnia zespół na początku sprintu)",
        "",
        "| Element sprintu | Owner | Recenzent |",
        "| --- | --- | --- |",
        "| _do uzupełnienia_ | | |",
        "",
        "Integrator sprintu: _do uzupełnienia_",
        "",
        "## Pełny opis",
        "",
        f"Plik `docs/sprints/SPRINT_{number}.md` w repozytorium.",
    ]
    return "\n".join(body) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generowanie github_issues/ z docs/sprints/.")
    parser.add_argument("--check", action="store_true", help="tylko sprawdź aktualność plików")
    args = parser.parse_args(argv)

    outdated = []
    for number in SPRINTS:
        sprint_path = ROOT / "docs" / "sprints" / f"SPRINT_{number}.md"
        sprint_text = sprint_path.read_text(encoding="utf-8")
        content = render_issue(number, sprint_text)
        target = ROOT / "github_issues" / f"{number:02d}_sprint_{number}.md"
        current = target.read_text(encoding="utf-8") if target.is_file() else None
        if current == content:
            continue
        outdated.append(target.name)
        if not args.check:
            target.write_text(content, encoding="utf-8")
    if args.check and outdated:
        print(f"Nieaktualne pliki github_issues/: {outdated}.")
        print("Uruchom: python scripts/build_issues.py")
        return 1
    print("github_issues/: aktualne" if not outdated else f"Zapisano: {outdated}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
