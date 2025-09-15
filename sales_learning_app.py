"""Simple sales learning application using linear regression.

This script trains a linear regression model on synthetic advertising data
and evaluates its ability to predict sales.
"""

from __future__ import annotations

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split


def generate_sales_data(n_samples: int = 50, random_state: int | None = 42) -> tuple[np.ndarray, np.ndarray]:
    """Generate a synthetic dataset of advertising spend and discount vs sales."""
    rng = np.random.default_rng(random_state)
    advertising = rng.uniform(0, 100, size=n_samples)
    discount = rng.uniform(0, 30, size=n_samples)
    sales = 0.5 * advertising + 2.0 * discount + rng.normal(scale=10, size=n_samples)
    features = np.column_stack([advertising, discount])
    return features, sales


def train_and_evaluate() -> None:
    X, y = generate_sales_data()
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0)
    model = LinearRegression()
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    print(f"Mean absolute error: {mean_absolute_error(y_test, predictions):.2f}")
    print(f"R^2 score: {r2_score(y_test, predictions):.2f}")


if __name__ == "__main__":
    train_and_evaluate()
