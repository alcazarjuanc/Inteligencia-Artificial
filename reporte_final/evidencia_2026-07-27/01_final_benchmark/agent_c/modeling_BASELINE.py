"""Small reproducible classification workflow."""


def load_dataset(path, target_column):
    raise NotImplementedError


def split_dataset(X, y, test_size=0.25, random_state=42):
    raise NotImplementedError


def build_model(random_state=42):
    raise NotImplementedError


def train_model(model, X_train, y_train):
    raise NotImplementedError


def evaluate_model(model, X_test, y_test):
    raise NotImplementedError


def predict(model, X):
    raise NotImplementedError
