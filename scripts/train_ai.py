"""
train_ai.py
===========
Trains the local AI risk-classification model (Random Forest) from the
synthetic AI-training dataset and saves it to models/risk_model.pkl.

Usage:
    python scripts/train_ai.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.ai_engine import AIEngine  # noqa: E402


def main():
    print("SecureDT - AI Risk Model Trainer")
    print("=" * 40)
    ai = AIEngine()
    if not os.path.exists(ai.dataset_path):
        print(f"Training dataset not found: {ai.dataset_path}")
        print("Run:  python scripts/generate_dataset.py")
        return 1
    print(f"Training on: {ai.dataset_path}")
    ai.train(ai.dataset_path)
    print(f"Model saved to: {ai.model_path}")
    print("Evaluation (on real held-out data):")
    m = ai.metrics
    if m:
        for k, v in m.items():
            print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
