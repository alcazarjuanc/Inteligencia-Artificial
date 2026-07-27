"""CSV ingestion and preprocessing utilities."""

import csv
import copy


def load_csv(path):
    """Load a UTF-8 CSV file and return a list of dicts preserving row order."""
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [dict(row) for row in reader]


def validate_schema(rows, required_columns):
    """Return True only when every row contains every required column."""
    for row in rows:
        for col in required_columns:
            if col not in row:
                return False
    return True


def remove_duplicates(rows, key_columns=None):
    """Return a new list with duplicates removed, preserving first occurrence and order.

    key_columns=None compares complete rows; otherwise compares requested columns.
    """
    seen = set()
    result = []
    for row in rows:
        if key_columns is None:
            key = tuple(sorted(row.items()))
        else:
            key = tuple(row[c] for c in key_columns)
        if key not in seen:
            seen.add(key)
            result.append(row)
    return result


def _is_missing(val):
    """Return True if a value is None, empty string, or whitespace-only."""
    return val is None or (isinstance(val, str) and val.strip() == "")


def handle_missing_numeric(rows, columns):
    """Impute missing numeric values with column means.

    Missing: None, empty, or whitespace.
    Convert nonmissing requested values to float.
    Return new dictionaries without mutating input.
    """
    # First pass: collect usable values per column to compute means
    col_sums = {c: 0.0 for c in columns}
    col_counts = {c: 0 for c in columns}
    for row in rows:
        for c in columns:
            val = row.get(c)
            if _is_missing(val):
                continue
            try:
                col_sums[c] += float(val)
                col_counts[c] += 1
            except (ValueError, TypeError):
                raise ValueError(f"Invalid numeric data in column '{c}'")

    for c in columns:
        if col_counts[c] == 0:
            raise ValueError(f"No usable values in column '{c}'")

    col_means = {c: col_sums[c] / col_counts[c] for c in columns}

    # Second pass: build new rows with imputed values
    result = []
    for row in rows:
        new_row = dict(row)
        for c in columns:
            val = row.get(c)
            if _is_missing(val):
                new_row[c] = col_means[c]
            else:
                try:
                    new_row[c] = float(val)
                except (ValueError, TypeError):
                    raise ValueError(f"Invalid numeric data in column '{c}'")
        result.append(new_row)
    return result


def numeric_summary(rows, columns):
    """Return a summary dict for each requested column.

    Ignores missing values. Converts numeric values to float.
    ValueError if a requested column has no usable values.
    """
    result = {}
    for c in columns:
        values = []
        for row in rows:
            val = row.get(c)
            if _is_missing(val):
                continue
            try:
                values.append(float(val))
            except (ValueError, TypeError):
                raise ValueError(f"Invalid numeric data in column '{c}'")
        if not values:
            raise ValueError(f"No usable values in column '{c}'")
        result[c] = {
            "count": len(values),
            "mean": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
        }
    return result
