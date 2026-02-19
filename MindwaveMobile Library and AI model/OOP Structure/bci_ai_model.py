import pandas as pd
import os
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.metrics import accuracy_score

class BCIModel:
    def __init__(self, model_path="bci_rf_model.joblib"):
        self.model_path = model_path
        self.model = None
        self.features = [
            "delta", "theta", "low_alpha", "high_alpha", 
            "low_beta", "high_beta", "low_gamma", "mid_gamma",
            "attention", "meditation"
        ]

    def train_from_csv(self, csv_path):
        """Trains the model using a Grid Search for the best parameters."""
        if not os.path.exists(csv_path):
            print(f"Error: {csv_path} not found. Cannot train.")
            return

        print("Loading data and starting Grid Search training...")
        data = pd.read_csv(csv_path)
        
        # X = Features (EEG bands), y = Labels (Forward, Stop, etc.)
        X = data[self.features]
        y = data["label"]

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Define the Grid of parameters to test
        param_grid = {
            'n_estimators': [50, 100, 200],
            'max_depth': [None, 10, 20],
            'min_samples_split': [2, 5]
        }

        rf = RandomForestClassifier(random_state=42)
        grid_search = GridSearchCV(estimator=rf, param_grid=param_grid, cv=5, n_jobs=-1)
        
        grid_search.fit(X_train, y_train)
        
        self.model = grid_search.best_estimator_
        
        # Test the quality
        predictions = self.model.predict(X_test)
        print(f"Training Complete! Accuracy: {accuracy_score(y_test, predictions):.2f}")
        print(f"Best Parameters: {grid_search.best_params_}")

        # Save the model
        joblib.dump(self.model, self.model_path)
        print(f"Model saved to {self.model_path}")

    def load_or_train(self, csv_path):
        """Checks if a model exists. If not, it trains a new one."""
        if os.path.exists(self.model_path):
            print(f"Loading existing model from {self.model_path}")
            self.model = joblib.load(self.model_path)
        else:
            print("No model found.")
            self.train_from_csv(csv_path)

    def predict(self, current_state_dict):
        """Takes the current state from SignalReader and returns a prediction."""
        if self.model is None:
            return "NO_MODEL"
        
        # Convert the dictionary state into a 2D array for the RF model
        df = pd.DataFrame([current_state_dict])[self.features]
        return self.model.predict(df)[0]