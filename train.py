import os
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib

print("==================================================")
print("--- Training Synthetic Educational Demo Models ---")
print("==================================================")

script_dir = os.path.dirname(os.path.abspath(__file__))
models_dir = os.path.join(script_dir, "models")
os.makedirs(models_dir, exist_ok=True)

np.random.seed(42)
n_samples = 1500

# 1. Parkinson's Disease synthetic-label demo model
print("Training synthetic-label Parkinson's demo model...")
age_p = np.random.normal(62, 8, n_samples).clip(40, 90)
updrs_p = np.random.normal(25, 12, n_samples).clip(0, 90)
moca_p = np.random.normal(26, 3, n_samples).clip(10, 30)
dat_p = np.random.normal(1.2, 0.4, n_samples).clip(0.2, 2.5)

p_risk = (((updrs_p > 30) & (dat_p < 0.85)) | ((moca_p < 23) & (dat_p < 0.85))).astype(int)
noise_idx = np.random.choice(n_samples, size=int(n_samples*0.03), replace=False)
p_risk[noise_idx] = 1 - p_risk[noise_idx]

X_p = np.column_stack([age_p, updrs_p, moca_p, dat_p])
model_p = RandomForestClassifier(n_estimators=200, random_state=42)
model_p.fit(X_p, p_risk)
joblib.dump(model_p, os.path.join(models_dir, "rf_pd_engine.pkl"))

# 2. Alzheimer's Disease synthetic-label demo model
print("Training synthetic-label Alzheimer's demo model...")
age_a = np.random.normal(72, 7, n_samples).clip(50, 95)
mmse_a = np.random.normal(24, 4, n_samples).clip(5, 30)
hipp_a = np.random.normal(6.5, 1.2, n_samples).clip(3.0, 10.0)
csf_a = np.random.normal(600, 200, n_samples).clip(200, 1100)

a_risk = ((mmse_a < 23) & (hipp_a < 5.2) & (csf_a < 450)).astype(int)
noise_idx_a = np.random.choice(n_samples, size=int(n_samples*0.03), replace=False)
a_risk[noise_idx_a] = 1 - a_risk[noise_idx_a]

X_a = np.column_stack([age_a, mmse_a, hipp_a, csf_a])
model_a = RandomForestClassifier(n_estimators=200, random_state=42)
model_a.fit(X_a, a_risk)
joblib.dump(model_a, os.path.join(models_dir, "rf_ad_engine.pkl"))

# 3. Huntington's Disease synthetic-label demo model
print("Training synthetic-label Huntington's demo model...")
age_h = np.random.normal(45, 12, n_samples).clip(20, 80)
cag_h = np.random.choice([32,34,35,36,38,40,42,45,50,55], size=n_samples, p=[0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1])
uhdrs_h = np.random.normal(20, 14, n_samples).clip(0, 90)
func_h = np.random.normal(10, 2.5, n_samples).clip(0, 13)

h_risk = ((cag_h >= 40) & ((uhdrs_h > 18) | (func_h < 8))).astype(int)
noise_idx_h = np.random.choice(n_samples, size=int(n_samples*0.03), replace=False)
h_risk[noise_idx_h] = 1 - h_risk[noise_idx_h]

X_h = np.column_stack([age_h, cag_h, uhdrs_h, func_h])
model_h = RandomForestClassifier(n_estimators=200, random_state=42)
model_h.fit(X_h, h_risk)
joblib.dump(model_h, os.path.join(models_dir, "rf_hd_engine.pkl"))

print("\n==================================================")
print("SUCCESS: Synthetic educational demo models saved to /models/")
print("==================================================")
