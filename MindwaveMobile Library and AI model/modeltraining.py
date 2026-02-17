from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import numpy as np
from joblib import dump, load
import pandas as pd

# backward = pd.read_csv("Readings/backward.csv")
# forward = pd.read_csv("Readings/forward.csv")
# dataset = pd.concat([forward,backward],ignore_index=True)
# task_to_class = {
    # "f" :0,
    # "b" :1
# }
# dataset["command_encoded"] = dataset["command"].map(task_to_class)
# dataset = dataset.drop(columns=["poor_signal"])
# dataset.to_csv("eye_movements.csv",index=False)

combined = pd.read_csv("eye_movements.csv")

features = ["delta","theta"]
X = combined[features]
y = combined['command_encoded']

scalar_final = StandardScaler()
X_scaled = scalar_final.fit_transform(X)
model = RandomForestClassifier(n_estimators=200,max_depth=None,random_state=42)
model.fit(X_scaled,y)
dump({
    'model':model,
    'scaler':scalar_final
},"eye_move_model.joblib")

