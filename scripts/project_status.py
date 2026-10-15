"""Stan projektu dla CI (format key=value, dopisywany do $GITHUB_OUTPUT)."""

import sys

from asi_project.config import load_project_config


def main() -> int:
    config = load_project_config()
    status = {
        "dataset_selected": config.dataset_selected,
        "sample_present": config.ci_sample_path.is_file(),
        "baseline_done": config.metrics_path.is_file(),
    }
    for key, value in status.items():
        print(f"{key}={'true' if value else 'false'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
