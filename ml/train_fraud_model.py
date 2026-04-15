import pandas as pd
import numpy as np
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, accuracy_score

# Load dataset
df = pd.read_csv("ml/fraud_data_realistic.csv")

feature_cols = [
    "gps_natural_travel",
    "accelerometer_active",
    "pressure_consistency",
    "cell_tower_match",
    "work_history_match",
    "no_active_order"
]
X = df[feature_cols].values
y = df["is_fraud"].values

# Add label noise (flip 5% of labels randomly) – simulates real-world mislabeling
np.random.seed(42)
noise_mask = np.random.random(len(y)) < 0.05
y[noise_mask] = 1 - y[noise_mask]

# Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Logistic regression with strong regularization (prevents overfitting)
model = LogisticRegression(C=0.01, max_iter=1000, random_state=42)
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
print("Test Accuracy:", accuracy_score(y_test, y_pred))
print("\nClassification Report:\n", classification_report(y_test, y_pred))

# Cross-validation (more honest estimate)
cv_scores = cross_val_score(model, X, y, cv=5, scoring='accuracy')
print(f"\n5-Fold Cross-Validation Accuracy: {cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})")

# Save model
joblib.dump(model, "ml/fraud_model.pkl")
joblib.dump(feature_cols, "ml/feature_names.pkl")
print("\nModel saved to ml/fraud_model.pkl")