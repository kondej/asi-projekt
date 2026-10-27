"""Model preprocessing i modele bazowe (Sprint 1).

Model preprocessing (imputacja, skalowanie, kodowanie — wszystko, co wymaga ``fit``) żyje
wewnątrz sklearn Pipeline. Dzięki temu przy predykcji wykonują się dokładnie te same kroki,
które zostały dopasowane na X_train, a cały model można zapisać jako jeden artefakt.
"""

from collections.abc import Sequence

from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def make_dummy() -> DummyClassifier:
    """Baseline bez wiedzy o cechach: zawsze przewiduje najczęstszą klasę z X_train."""
    return DummyClassifier(strategy="most_frequent")


def build_baseline_pipeline(
    numeric_features: Sequence[str],
    categorical_features: Sequence[str],
) -> Pipeline:
    """Pipeline = model preprocessing (ColumnTransformer) + LogisticRegression.

    - cechy numeryczne: imputacja medianą i standaryzacja,
    - cechy kategoryczne: imputacja najczęstszą wartością i kodowanie one-hot
      (kategorie niewidziane w treningu są ignorowane przy predykcji),
    - ostatni krok: LogisticRegression (ma ``predict_proba``).

    Wszystkie kroki uczące się z danych są dopasowywane wyłącznie na danych przekazanych
    do ``fit`` (czyli na X_train).
    """
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ],
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore")),
        ],
    )
    preprocessing = ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, list(numeric_features)),
            ("categorical", categorical_pipeline, list(categorical_features)),
        ],
    )
    return Pipeline(
        steps=[
            ("preprocessing", preprocessing),
            ("model", LogisticRegression(max_iter=1000)),
        ],
    )
