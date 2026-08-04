from dataclasses import dataclass

from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_extraction import DictVectorizer
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.pipeline import Pipeline


@dataclass(frozen=True)
class FittedMLModel:
    model: Pipeline
    mae: float
    r2_score: float
    accuracy_score: float
    feature_importance: dict[str, float]


def fit_service_time_model(rows: list[dict[str, object]]) -> FittedMLModel:
    features = [row["features"] for row in rows]
    actuals = [float(row["duration_minutes"]) for row in rows]
    model = Pipeline(steps=[
        ("features", DictVectorizer(sparse=False)),
        ("regressor", RandomForestRegressor(n_estimators=100, random_state=42, min_samples_leaf=1)),
    ])
    model.fit(features, actuals)
    predictions = [float(value) for value in model.predict(features)]
    mae = float(mean_absolute_error(actuals, predictions))
    r2 = float(r2_score(actuals, predictions)) if len(set(actuals)) > 1 else 0.0
    mean_actual = sum(actuals) / len(actuals)
    accuracy = max(0.0, min(1.0, 1 - (mae / mean_actual))) if mean_actual else 0.0

    grouped: dict[str, float] = {}
    vectorizer = model.named_steps["features"]
    regressor = model.named_steps["regressor"]
    for name, importance in zip(vectorizer.get_feature_names_out(), regressor.feature_importances_):
        base_name = name.split("=", 1)[0]
        grouped[base_name] = grouped.get(base_name, 0.0) + float(importance)
    return FittedMLModel(model, mae, r2, accuracy, dict(sorted(grouped.items())))
