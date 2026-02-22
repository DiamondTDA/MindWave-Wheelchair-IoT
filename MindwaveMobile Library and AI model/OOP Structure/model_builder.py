import pandas as pd
from sklearn.utils import shuffle
from bci_ai_model import BCIModel

def prepare_and_train():
    print("1. Merging, Cleaning, and Shuffling Data...")
    try:
        df_n = pd.read_csv('Readings/Neutral.csv')
        df_f = pd.read_csv('Readings/Forward.csv')
    except FileNotFoundError:
        print("Error: Please make sure Neutral.csv and Forward.csv are in this folder.")
        return

    # Combine the files
    df_combined = pd.concat([df_n, df_f], ignore_index=True)
    
    # Drop the columns that the AI doesn't need
    drop_cols = ['timestamp', 'poor_signal', 'total_latency(ms)', 'logic_time(ms)', 'blink']
    df_clean = df_combined.drop(columns=[col for col in drop_cols if col in df_combined.columns])

    # Shuffle so the model doesn't just memorize the order
    df_shuffled = shuffle(df_clean, random_state=42).reset_index(drop=True)
    
    # Save it to a temporary master training file
    master_csv_path = 'master_training_data.csv'
    df_shuffled.to_csv(master_csv_path, index=False)
    print(f"Data prepped, cleaned, and saved to {master_csv_path}\n")

    # 2. Initialize and Train your model
    print("2. Firing up the BCI Model...")
    ai = BCIModel(model_path="test_rf_model.joblib")
    
    # This will trigger your GridSearch and print the accuracy!
    ai.train_from_csv(master_csv_path)

if __name__ == "__main__":
    prepare_and_train()