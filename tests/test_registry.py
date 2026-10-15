"""Rejestr datasetów (kontrakt prowadzącej) i jego zgodność z docs/datasets.md."""

from asi_project.config import SPLIT_STRATEGIES


def test_registry_lists_approved_datasets(registry):
    assert 3 <= len(registry) <= 4, "Lista dla studentów ma 3–4 datasety."


def test_every_contract_is_internally_consistent(registry):
    for dataset_id, contract in registry.items():
        allowed = set(contract.allowed_features)
        excluded = set(contract.excluded_features)
        assert allowed, f"{dataset_id}: pusta lista ALLOWED FEATURES"
        assert len(allowed) == len(contract.allowed_features), f"{dataset_id}: duplikaty"
        assert not allowed & excluded, f"{dataset_id}: kolumna jednocześnie ALLOWED i EXCLUDED"
        assert contract.target not in allowed | excluded, f"{dataset_id}: target jako cecha"
        assert contract.positive_class, f"{dataset_id}: brak klasy pozytywnej"
        assert contract.split_strategy in SPLIT_STRATEGIES
        assert contract.prediction_moment, f"{dataset_id}: brak momentu predykcji"
        assert all(reason.strip() for reason in contract.excluded_features.values())
        assert contract.download_url.startswith("https://archive.ics.uci.edu/")
        assert contract.doi.startswith("https://doi.org/")
        assert contract.license == "CC BY 4.0"


def test_docs_describe_every_dataset_and_column(registry, repo_root):
    docs = (repo_root / "docs" / "datasets.md").read_text(encoding="utf-8")
    for dataset_id, contract in registry.items():
        assert f"`{dataset_id}`" in docs, f"docs/datasets.md nie opisuje {dataset_id}"
        columns = [contract.target, *contract.allowed_features, *contract.excluded_features]
        missing = [column for column in columns if f"`{column}`" not in docs]
        assert not missing, f"{dataset_id}: kolumny bez opisu w docs/datasets.md: {missing}"


def test_project_yaml_is_well_formed(project_config, registry):
    assert project_config.dataset_id is None or project_config.dataset_id in registry
    assert 0.0 < project_config.test_size < 1.0
    assert isinstance(project_config.random_state, int)
