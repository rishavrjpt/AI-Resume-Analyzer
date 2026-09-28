"""
Training script for ResumeLens AI section classifier.
Trains on data/processed/section_train.csv and validates on data/processed/section_val.csv.
Saves model artifacts to models/ and training metadata.
"""

import os
import sys
import json
import datetime

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
import sklearn
from sklearn.metrics import classification_report, f1_score
from src.models.section_classifier import MLSectionClassifier, CANONICAL_SECTIONS


def train(
    train_path: str = "data/processed/section_train.csv",
    val_path: str = "data/processed/section_val.csv",
    model_output_path: str = "models/section_classifier.joblib",
    metadata_output_path: str = "models/model_metadata.json"
):
    print("=" * 60)
    print("ResumeLens AI — Model Training")
    print("=" * 60)

    if not os.path.exists(train_path):
        raise FileNotFoundError(
            f"Training dataset not found at {train_path}. Run 'python src/data/prepare_dataset.py' first."
        )

    train_df = pd.read_csv(train_path)
    print(f"Loaded {len(train_df)} training samples across {train_df['document_id'].nunique()} source documents.")

    X_train = train_df["text"].astype(str).tolist()
    y_train = train_df["label"].astype(str).tolist()

    # Initialize and train ML classifier
    classifier = MLSectionClassifier(c_param=2.0, max_features=3500)
    print("Fitting TF-IDF Vectorizer and Multinomial Logistic Regression...")
    classifier.fit(X_train, y_train)

    # Validate if validation set exists
    val_metrics = {}
    if os.path.exists(val_path):
        val_df = pd.read_csv(val_path)
        print(f"Loaded {len(val_df)} validation samples across {val_df['document_id'].nunique()} source documents.")
        X_val = val_df["text"].astype(str).tolist()
        y_val = val_df["label"].astype(str).tolist()

        y_pred = classifier.predict(X_val)
        val_macro_f1 = f1_score(y_val, y_pred, average="macro", zero_division=0)
        val_report = classification_report(y_val, y_pred, output_dict=True, zero_division=0)
        print(f"Validation Macro F1 Score: {val_macro_f1:.4f}")
        val_metrics = {
            "validation_samples": len(val_df),
            "macro_f1": float(val_macro_f1),
            "classification_report": val_report
        }

    # Save trained model
    os.makedirs(os.path.dirname(model_output_path), exist_ok=True)
    classifier.save(model_output_path)
    print(f"Saved trained model artifact to {model_output_path}")

    # Save model metadata
    metadata = {
        "model_name": "ResumeLens-Section-Classifier",
        "model_version": "1.0.0",
        "model_type": "TF-IDF (1-3 grams) + Class-Weighted Logistic Regression",
        "training_date": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "sklearn_version": sklearn.__version__,
        "dataset_name": "ResumeLens Curated Resume Section Corpus",
        "train_samples": len(train_df),
        "train_documents": int(train_df["document_id"].nunique()),
        "classes": CANONICAL_SECTIONS,
        "validation_metrics": val_metrics,
        "hyperparameters": {
            "c_param": classifier.c_param,
            "max_features": classifier.max_features,
            "class_weight": "balanced",
            "ngram_range": [1, 3]
        }
    }

    with open(metadata_output_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"Saved model metadata to {metadata_output_path}")
    print("=" * 60)
    print("Training successfully completed!")
    return metadata


if __name__ == "__main__":
    train()
