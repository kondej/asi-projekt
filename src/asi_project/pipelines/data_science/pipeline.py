"""Pipeline data_science: split -> trening -> ewaluacja (Sprint 2)."""

from kedro.pipeline import Pipeline, node

from asi_project.pipelines.data_science.nodes import (
    build_model_package,
    evaluate_models,
    make_features_target,
    run_experiments,
    split_data,
    train_models,
)


def create_pipeline(**kwargs) -> Pipeline:
    """Składa nody w pipeline; nazwy datasetów odpowiadają wpisom w conf/base/catalog.yml."""
    return Pipeline(
        [
            node(
                func=make_features_target,
                inputs=["training_data", "params:dataset", "params:features"],
                outputs=["X", "y"],
                name="make_features_target",
            ),
            node(
                func=split_data,
                inputs=["X", "y", "params:dataset", "params:split"],
                outputs=["X_train", "X_test", "y_train", "y_test"],
                name="split_data",
            ),
            node(
                func=train_models,
                inputs=["X_train", "y_train", "params:features"],
                outputs=["model", "dummy_model"],
                name="train_models",
            ),
            node(
                func=evaluate_models,
                inputs=[
                    "model",
                    "dummy_model",
                    "X_train",
                    "X_test",
                    "y_test",
                    "params:dataset",
                    "params:features",
                    "params:split",
                    "params:data_mode",
                ],
                outputs="metrics",
                name="evaluate_models",
            ),
            node(
                func=run_experiments,
                inputs=[
                    "model",
                    "X_train",
                    "X_test",
                    "y_train",
                    "y_test",
                    "metrics",
                    "params:dataset",
                    "params:features",
                    "params:data_mode",
                    "params:experiments",
                    "params:model_package_path",
                    "params:production_model",
                ],
                outputs="experiment_comparison",
                name="run_experiments",
            ),
            node(
                func=build_model_package,
                inputs=[
                    "model",
                    "metrics",
                    "params:dataset",
                    "params:features",
                    "params:data_mode",
                    "params:model_package_path",
                    "params:production_model",
                    "experiment_comparison",
                ],
                outputs="model_package_metadata",
                name="build_model_package",
            ),
        ],
    )
