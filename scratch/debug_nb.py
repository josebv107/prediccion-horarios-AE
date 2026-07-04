import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import predictor
from predictor import FEATURE_ORDER

print("--- MODEL FEATURE MEANS PER CLASS ---")
# Classes are usually: ['Bueno', 'Deficiente', 'Excelente', 'Regular']
classes = predictor._model.classes_

# Print header
header = f"{'Feature':<35} | " + " | ".join([f"{c:<10}" for c in classes])
print(header)
print("-" * len(header))

for j, feat_name in enumerate(FEATURE_ORDER):
    means = [predictor._model.theta_[idx][j] for idx in range(len(classes))]
    row = f"{feat_name:<35} | " + " | ".join([f"{m:<10.4f}" for m in means])
    print(row)
