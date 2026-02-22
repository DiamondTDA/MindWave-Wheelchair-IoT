import pandas as pd
import joblib
import os
from collections import Counter

def evaluate_new_data(csv_path, model_path="test_rf_model.joblib"):
    # 1. Check if files exist
    if not os.path.exists(model_path):
        print(f"Error: Model not found at {model_path}")
        return
    if not os.path.exists(csv_path):
        print(f"Error: Data file not found at {csv_path}")
        return

    # 2. Load the trained model
    print(f"Loading model from {model_path}...")
    model = joblib.load(model_path)

    # 3. Load the new 10-second test data
    print(f"Loading test data from {csv_path}...\n")
    df = pd.read_csv(csv_path)

    # 4. Extract the exact features the model was trained on
    features = [
        "delta", "theta", "low_alpha", "high_alpha", 
        "low_beta", "high_beta", "low_gamma", "mid_gamma",
        "attention", "meditation"
    ]
    
    # Ensure all required columns are in the new CSV
    missing_cols = [col for col in features if col not in df.columns]
    if missing_cols:
        print(f"Error: Missing columns in CSV: {missing_cols}")
        return

    X_new = df[features]

    # 5. Make Predictions
    predictions = model.predict(X_new)
    
    # 6. Analyze the Results
    total_rows = len(predictions)
    counts = Counter(predictions)
    
    print("========================================")
    print("🧠 LIVE PREDICTION RESULTS (10 Seconds)")
    print("========================================")
    print(f"Total readings analyzed: {total_rows}\n")
    
    for label, count in counts.items():
        percentage = (count / total_rows) * 100
        print(f"Predicted '{label}': {count} times ({percentage:.1f}%)")
        
    # If the file happens to have a 'label' column, calculate real metrics
    if 'label' in df.columns:
        from sklearn.metrics import accuracy_score, f1_score
        y_true = df['label']
        acc = accuracy_score(y_true, predictions)
        
        # Determine the positive label dynamically based on what's in the true labels
        pos_label = 'F' if 'F' in y_true.values else y_true.unique()[0]
        
        try:
            f1 = f1_score(y_true, predictions, pos_label=pos_label)
            print("\n--- Ground Truth Evaluation ---")
            print(f"Actual Accuracy: {acc * 100:.2f}%")
            print(f"F1-Score: {f1:.2f}")
        except Exception:
            pass # Skips F1 if there's a label mismatch issue in a pure 1-label test set

if __name__ == "__main__":
    # Change 'forward_test_10s.csv' to whatever you name your new file
    evaluate_new_data(csv_path="Readings/Forward10s.csv", model_path="test_rf_model.joblib")