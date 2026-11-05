"""
Training Pipeline for SkyPlan AI Machine Learning Models:
- Model A: Rainout Risk Prediction (Random Forest Classifier)
- Model B: Heat Risk Prediction (Random Forest Classifier)

Evaluates accuracy, precision, recall, F1-score, and confusion matrix.
Saves models, scalers, and performance metadata for production inference.
"""

import json
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, precision_recall_fscore_support

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "ml" / "datasets"
MODELS_DIR = BASE_DIR / "trained_models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

CLASS_NAMES = ["Low Risk", "Moderate Risk", "High Risk"]

def train_rainout_model():
    print("\n" + "="*50)
    print("TRAINING MODEL A: RAINOUT RISK PREDICTION")
    print("="*50)
    
    csv_path = DATA_DIR / "rainout_dataset.csv"
    df = pd.read_csv(csv_path)
    
    feature_cols = ["temperature", "humidity", "rain_probability", "rainfall_mm", "wind_speed"]
    X = df[feature_cols]
    y = df["risk_level"]
    
    # Train-Test Split (80/20 stratified)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    
    # Feature Scaling
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Random Forest Classifier
    clf = RandomForestClassifier(
        n_estimators=120,
        max_depth=12,
        min_samples_split=4,
        min_samples_leaf=2,
        random_state=42,
        class_weight="balanced"
    )
    clf.fit(X_train_scaled, y_train)
    
    # Evaluation
    y_pred = clf.predict(X_test_scaled)
    acc = accuracy_score(y_test, y_pred)
    prec, rec, f1, _ = precision_recall_fscore_support(y_test, y_pred, average="weighted")
    cm = confusion_matrix(y_test, y_pred, labels=CLASS_NAMES)
    
    report = classification_report(y_test, y_pred, labels=CLASS_NAMES, output_dict=True)
    
    print(f"Accuracy: {acc*100:.2f}%")
    print(f"Precision: {prec:.4f}")
    print(f"Recall:    {rec:.4f}")
    print(f"F1-Score:  {f1:.4f}")
    print("\nConfusion Matrix (Low, Moderate, High):")
    print(cm)
    
    # Feature importances
    importances = dict(zip(feature_cols, [round(float(x), 4) for x in clf.feature_importances_]))
    print("\nFeature Importances:", importances)
    
    # Save artifacts
    model_path = MODELS_DIR / "rainout_model.joblib"
    scaler_path = MODELS_DIR / "rainout_scaler.joblib"
    joblib.dump(clf, model_path)
    joblib.dump(scaler, scaler_path)
    print(f"Saved Rainout Model to: {model_path}")
    
    return {
        "model_name": "Rainout Risk Classifier",
        "algorithm": "Random Forest",
        "accuracy": round(float(acc), 4),
        "precision": round(float(prec), 4),
        "recall": round(float(rec), 4),
        "f1_score": round(float(f1), 4),
        "features": feature_cols,
        "feature_importances": importances,
        "classes": CLASS_NAMES,
        "confusion_matrix": cm.tolist(),
        "classification_report": report
    }

def train_heat_model():
    print("\n" + "="*50)
    print("TRAINING MODEL B: HEAT RISK PREDICTION")
    print("="*50)
    
    csv_path = DATA_DIR / "heat_dataset.csv"
    df = pd.read_csv(csv_path)
    
    feature_cols = ["temperature", "humidity", "wind_speed", "heat_index"]
    X = df[feature_cols]
    y = df["risk_level"]
    
    # Train-Test Split (80/20 stratified)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=101, stratify=y
    )
    
    # Feature Scaling
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Random Forest Classifier
    clf = RandomForestClassifier(
        n_estimators=120,
        max_depth=10,
        min_samples_split=4,
        min_samples_leaf=2,
        random_state=101,
        class_weight="balanced"
    )
    clf.fit(X_train_scaled, y_train)
    
    # Evaluation
    y_pred = clf.predict(X_test_scaled)
    acc = accuracy_score(y_test, y_pred)
    prec, rec, f1, _ = precision_recall_fscore_support(y_test, y_pred, average="weighted")
    cm = confusion_matrix(y_test, y_pred, labels=CLASS_NAMES)
    
    report = classification_report(y_test, y_pred, labels=CLASS_NAMES, output_dict=True)
    
    print(f"Accuracy: {acc*100:.2f}%")
    print(f"Precision: {prec:.4f}")
    print(f"Recall:    {rec:.4f}")
    print(f"F1-Score:  {f1:.4f}")
    print("\nConfusion Matrix (Low, Moderate, High):")
    print(cm)
    
    # Feature importances
    importances = dict(zip(feature_cols, [round(float(x), 4) for x in clf.feature_importances_]))
    print("\nFeature Importances:", importances)
    
    # Save artifacts
    model_path = MODELS_DIR / "heat_model.joblib"
    scaler_path = MODELS_DIR / "heat_scaler.joblib"
    joblib.dump(clf, model_path)
    joblib.dump(scaler, scaler_path)
    print(f"Saved Heat Model to: {model_path}")
    
    return {
        "model_name": "Heat Risk Classifier",
        "algorithm": "Random Forest",
        "accuracy": round(float(acc), 4),
        "precision": round(float(prec), 4),
        "recall": round(float(rec), 4),
        "f1_score": round(float(f1), 4),
        "features": feature_cols,
        "feature_importances": importances,
        "classes": CLASS_NAMES,
        "confusion_matrix": cm.tolist(),
        "classification_report": report
    }

if __name__ == "__main__":
    rain_meta = train_rainout_model()
    heat_meta = train_heat_model()
    
    meta_path = MODELS_DIR / "model_metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": pd.Timestamp.now().isoformat(),
            "models": {
                "rainout": rain_meta,
                "heat": heat_meta
            }
        }, f, indent=2)
    print(f"\nSaved combined metadata to: {meta_path}")
    print("Training pipeline successfully finished!")

