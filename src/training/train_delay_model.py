"""
Train Random Forest model for delay prediction.

Features:
- Origin port, destination port
- Carrier name, carrier reliability
- Month, day of week
- Transit days
- Risk flag
- Seasonal and weekday factors

Target: will_delay (binary classification)
Goal: 70%+ accuracy
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report
)
import joblib
import json
import os


def load_training_data(filepath: str = "data/training_data.csv") -> pd.DataFrame:
    """Load training data from CSV."""
    print(f"📂 Loading training data from: {filepath}")
    df = pd.DataFrame(pd.read_csv(filepath))
    print(f"   Loaded {len(df)} samples")
    return df


def prepare_features(df: pd.DataFrame) -> tuple:
    """
    Prepare features and target for training.
    
    Returns:
        X (features), y (target), feature_names, encoders
    """
    print("\n🔧 Preparing features...")
    
    # Categorical encoders
    encoders = {}
    
    # Encode categorical features
    for col in ["origin_port", "destination_port", "carrier_name", "container_type"]:
        le = LabelEncoder()
        df[f"{col}_encoded"] = le.fit_transform(df[col])
        encoders[col] = le
        print(f"   Encoded {col}: {len(le.classes_)} unique values")
    
    # Select features for training
    feature_cols = [
        "origin_port_encoded",
        "destination_port_encoded",
        "carrier_name_encoded",
        "carrier_reliability",
        "month",
        "day_of_week",
        "transit_days",
        "container_type_encoded",
        "risk_flag",
        "base_delay_rate",
        "seasonal_factor",
        "weekday_factor",
    ]
    
    X = df[feature_cols].values
    y = df["will_delay"].astype(int).values
    
    print(f"   Features shape: {X.shape}")
    print(f"   Target distribution: {np.bincount(y)} (0=on_time, 1=delayed)")
    
    return X, y, feature_cols, encoders


def train_model(X, y, feature_names):
    """Train Random Forest classifier."""
    print("\n🌲 Training Random Forest model...")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"   Training set: {len(X_train)} samples")
    print(f"   Test set: {len(X_test)} samples")
    
    # Train model
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=10,
        min_samples_leaf=5,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)
    
    # Metrics
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    
    print(f"\n📊 Model Performance:")
    print(f"   Accuracy:  {accuracy:.3f}")
    print(f"   Precision: {precision:.3f}")
    print(f"   Recall:    {recall:.3f}")
    print(f"   F1 Score:  {f1:.3f}")
    
    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    print(f"\n   Confusion Matrix:")
    print(f"   [[TN={cm[0,0]}, FP={cm[0,1]}]")
    print(f"    [FN={cm[1,0]}, TP={cm[1,1]}]]")
    
    # Cross-validation
    print(f"\n🔄 Cross-Validation (5-fold)...")
    cv_scores = cross_val_score(model, X, y, cv=5, scoring='accuracy')
    print(f"   CV Scores: {cv_scores}")
    print(f"   CV Mean: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")
    
    # Feature importance
    print(f"\n🎯 Feature Importance:")
    feature_importance = sorted(
        zip(feature_names, model.feature_importances_),
        key=lambda x: x[1],
        reverse=True
    )
    for feat, importance in feature_importance[:10]:
        print(f"   {feat}: {importance:.4f}")
    
    # Classification report
    print(f"\n📋 Classification Report:")
    print(classification_report(y_test, y_pred, target_names=["on_time", "delayed"]))
    
    # Store metrics
    metrics = {
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1),
        "cv_mean": float(cv_scores.mean()),
        "cv_std": float(cv_scores.std()),
        "feature_importance": {
            feat: float(imp) for feat, imp in feature_importance
        }
    }
    
    return model, metrics, feature_importance


def save_model(model, encoders, feature_names, metrics, model_dir="models"):
    """Save trained model, encoders, and metadata."""
    print(f"\n💾 Saving model to: {model_dir}/")
    
    os.makedirs(model_dir, exist_ok=True)
    
    # Save model
    model_path = f"{model_dir}/delay_prediction_model.pkl"
    joblib.dump(model, model_path)
    print(f"   ✅ Model saved: {model_path}")
    
    # Save encoders
    encoders_path = f"{model_dir}/label_encoders.pkl"
    joblib.dump(encoders, encoders_path)
    print(f"   ✅ Encoders saved: {encoders_path}")
    
    # Save feature names
    features_path = f"{model_dir}/feature_names.json"
    with open(features_path, 'w') as f:
        json.dump(feature_names, f, indent=2)
    print(f"   ✅ Features saved: {features_path}")
    
    # Save metrics
    metrics_path = f"{model_dir}/model_metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"   ✅ Metrics saved: {metrics_path}")
    
    print(f"\n✅ Model training complete!")
    print(f"\n📁 Model artifacts:")
    print(f"   - {model_path}")
    print(f"   - {encoders_path}")
    print(f"   - {features_path}")
    print(f"   - {metrics_path}")


def main():
    """Main training pipeline."""
    print("=" * 70)
    print("🤖 Delay Prediction Model Training")
    print("=" * 70)
    
    # Load data
    df = load_training_data()
    
    # Prepare features
    X, y, feature_names, encoders = prepare_features(df)
    
    # Train model
    model, metrics, feature_importance = train_model(X, y, feature_names)
    
    # Save model
    save_model(model, encoders, feature_names, metrics)
    
    # Final summary
    print("\n" + "=" * 70)
    print("✅ TRAINING COMPLETE!")
    print("=" * 70)
    print(f"Model Accuracy: {metrics['accuracy']:.1%} (Goal: >70%)")
    if metrics['accuracy'] >= 0.70:
        print("✅ Goal achieved! Model ready for deployment.")
    else:
        print("⚠️  Below goal. Consider adding more features or data.")
    print("=" * 70)
    
    return model, metrics


if __name__ == "__main__":
    model, metrics = main()
