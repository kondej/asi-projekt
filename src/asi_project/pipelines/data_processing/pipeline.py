from kedro.pipeline import Pipeline, node, pipeline

from .nodes import filter_training_data, normalize_input_data, validate_raw_data


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=validate_raw_data,
                inputs=["raw_data", "parameters"],
                outputs="validated_data",
                name="validate_raw_data_node",
            ),
            node(
                func=normalize_input_data,
                inputs="validated_data",
                outputs="normalized_data",
                name="normalize_input_data_node",
            ),
            node(
                func=filter_training_data,
                inputs=["normalized_data", "parameters"],
                outputs="training_data",
                name="filter_training_data_node",
            ),
        ]
    )