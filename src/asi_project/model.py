"""Model preprocessing i modele bazowe (Sprint 1).

Model preprocessing (imputacja, skalowanie, kodowanie — wszystko, co wymaga ``fit``) żyje
wewnątrz sklearn Pipeline. Dzięki temu przy predykcji wykonują się dokładnie te same kroki,
które zostały dopasowane na X_train, a cały model można zapisać jako jeden artefakt.
"""

from collections.abc import Sequence

from sklearn.dummy import DummyClassifier
from sklearn.pipeline import Pipeline


def make_dummy() -> DummyClassifier:
    """Baseline bez wiedzy o cechach: zawsze przewiduje najczęstszą klasę z X_train."""
    return DummyClassifier(strategy="most_frequent")


def build_baseline_pipeline(
    numeric_features: Sequence[str],
    categorical_features: Sequence[str],
) -> Pipeline:
    """TODO (S1): Pipeline = model preprocessing (ColumnTransformer) + LogisticRegression.

    Wymagania (sprawdzane w tests/test_project.py):
    - Pipeline przyjmuje DataFrame z kolumnami ``numeric_features + categorical_features``,
    - cały model preprocessing jest wewnątrz Pipeline (bez wcześniejszego kodowania ręcznie),
    - braki danych i kategorie niewidziane w treningu nie przerywają predykcji,
    - ostatni krok ma ``predict_proba``,
    - wynik jest deterministyczny (dwa dopasowania na tych samych danych dają te same wyniki).

    Wzorzec znasz z drugich zajęć (notebook 02 onboardingu).
    """
    raise NotImplementedError(
        "TODO (S1): zaimplementuj build_baseline_pipeline w src/asi_project/model.py",
    )
