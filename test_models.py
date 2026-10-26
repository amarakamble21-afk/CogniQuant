import pandas as pd
import joblib

def test_all_models_and_metadata():
    print("=" * 60)
    print("1. TESTING HUNTINGTON'S DISEASE CLASSIFIER")
    print("=" * 60)
    try:
        clf_h = joblib.load('huntingtons_classifier_model.pkl')
        sample_input_h = pd.DataFrame({
            'Age': [45], 'Sex': ['Male'], 'Family_History': ['Yes'],
            'HTT_CAG_Repeat_Length': [48], 'Motor_Symptoms': ['Moderate'],
            'Cognitive_Decline': ['Unknown'], 'Chorea_Score': [5.2],
            'Brain_Volume_Loss': [3.1], 'Functional_Capacity': [85],
            'Gene_Mutation_Type': ['Deletion'], 'HTT_Gene_Expression_Level': [1.2],
            'Protein_Aggregation_Level': [0.65]
        })
        prediction = clf_h.predict(sample_input_h)[0]
        print(f" -> Predicted Disease Stage: {prediction}")
    except Exception as e:
        print(f"Error: {e}")

    print("\n" + "=" * 60)
    print("2. TESTING PARKINSON'S MOTOR UPDRS REGRESSOR")
    print("=" * 60)
    try:
        reg_p = joblib.load('parkinsons_regressor_model.pkl')
        sample_input_p = pd.DataFrame({
            'age': [68], 'sex': [0], 'test_time': [15.5], 'Jitter(%)': [0.0055],
            'Jitter(Abs)': [0.00003], 'Jitter:RAP': [0.003], 'Jitter:PPQ5': [0.0025],
            'Jitter:DDP': [0.009], 'Shimmer': [0.022], 'Shimmer(dB)': [0.21],
            'Shimmer:APQ3': [0.011], 'Shimmer:APQ5': [0.012], 'Shimmer:APQ11': [0.015],
            'Shimmer:DDA': [0.035], 'NHR': [0.012], 'HNR': [23.5], 'RPDE': [0.42],
            'DFA': [0.55], 'PPE': [0.15]
        })
        predicted_updrs = reg_p.predict(sample_input_p)[0]
        print(f" -> Predicted Motor UPDRS Score: {predicted_updrs:.2f}")
    except Exception as e:
        print(f"Error: {e}")

    print("\n" + "=" * 60)
    print("3. QUERYING ALZHEIMER'S ADNI IMAGING METADATA")
    print("=" * 60)
    try:
        # Load the merged ADNI metadata PKL
        meta_a = joblib.load('adni_merged_imaging_metadata.pkl')
        print(f"✓ Loaded ADNI Metadata successfully ({len(meta_a):,} records).")

        # Test querying for a specific subject ID or filter criteria
        test_subject_id = meta_a['subject_id'].iloc[0] # Pick the first subject as a test
        subject_records = meta_a[meta_a['subject_id'] == test_subject_id]

        print(f" -> Querying records for Subject ID: {test_subject_id}")
        print(f" -> Found {len(subject_records)} imaging session(s).")
        print(subject_records[['subject_id', 'image_visit', 'scanner_manufacturer', 'magnetic_field_strength', 'radiopharmaceutical']].head())

    except Exception as e:
        print(f"Error querying ADNI metadata: {e}")

if __name__ == "__main__":
    test_all_models_and_metadata()