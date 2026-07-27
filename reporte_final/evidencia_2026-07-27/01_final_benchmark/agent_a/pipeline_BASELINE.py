"""CSV ingestion and preprocessing utilities."""


def load_csv(path):
    raise NotImplementedError


def validate_schema(rows, required_columns):
    raise NotImplementedError


def remove_duplicates(rows, key_columns=None):
    raise NotImplementedError


def handle_missing_numeric(rows, columns):
    raise NotImplementedError


def numeric_summary(rows, columns):
    raise NotImplementedError
