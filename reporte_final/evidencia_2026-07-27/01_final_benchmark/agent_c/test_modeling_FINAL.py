import pandas as pd
import pytest
from sklearn.pipeline import Pipeline
from modeling import (
    load_dataset, split_dataset, build_model,
    train_model, evaluate_model, predict,
)

DATA = "data.csv"

def test_load_dataset_removes_target():
    X, y = load_dataset(DATA, "high_anxiety")
    assert "high_anxiety" not in X.columns
    assert list(y) == list(pd.read_csv(DATA)["high_anxiety"])

def test_load_dataset_invalid_target():
    with pytest.raises(ValueError):
        load_dataset(DATA, "no_such_column")

def test_split_dataset_stratified():
    X, y = load_dataset(DATA, "high_anxiety")
    X_tr, X_te, y_tr, y_te = split_dataset(X, y)
    assert len(X_tr) + len(X_te) == len(X)
    assert y_tr.value_counts(normalize=True).round(2).tolist() == y.value_counts(normalize=True).round(2).tolist()

def test_build_model_pipeline_structure():
    m = build_model()
    assert isinstance(m, Pipeline)
    assert "scaler" in m.named_steps
    assert "model" in m.named_steps

def test_build_model_random_state():
    m = build_model(random_state=99)
    assert m.named_steps["model"].random_state == 99

def test_train_model():
    X, y = load_dataset(DATA, "high_anxiety")
    X_tr, _, y_tr, _ = split_dataset(X, y)
    m = build_model()
    trained = train_model(m, X_tr, y_tr)
    assert trained is m

def test_evaluate_model_keys_types():
    X, y = load_dataset(DATA, "high_anxiety")
    _, X_te, _, y_te = split_dataset(X, y)
    m = train_model(build_model(), X, y)
    res = evaluate_model(m, X_te, y_te)
    assert set(res.keys()) == {"accuracy", "balanced_accuracy", "f1"}
    assert all(isinstance(res[k], float) for k in res)

def test_predict_returns_int_list():
    X, y = load_dataset(DATA, "high_anxiety")
    m = train_model(build_model(), X, y)
    out = predict(m, X)
    assert isinstance(out, list) and all(isinstance(v, int) for v in out)
