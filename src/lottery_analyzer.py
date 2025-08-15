import pandas as pd
import matplotlib.pyplot as plt
import os
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
import numpy as np

# --- Existing Frequency Analysis Functions (kept for context/comparison) ---

def get_number_frequencies(file_path):
    """
    Loads a CSV file, extracts all two-digit numbers from prize columns,
    and returns their frequencies.
    """
    df = pd.read_csv(file_path)

    all_numbers = pd.Series(dtype=str)
    for col in df.columns:
        if col not in ['date', 'province']:
            all_numbers = pd.concat([all_numbers, df[col].astype(str).str.zfill(2)])

    all_possible_numbers = [str(i).zfill(2) for i in range(100)]
    frequency = all_numbers.value_counts().reindex(all_possible_numbers, fill_value=0).sort_index()
    
    return frequency

def plot_frequencies(frequencies, region_code, output_image_path):
    """
    Plots the top 10 most frequent and top 10 least frequent numbers.
    """
    most_frequent = frequencies.sort_values(ascending=False).head(10)
    least_frequent = frequencies.sort_values(ascending=True).head(10)

    fig, axes = plt.subplots(2, 1, figsize=(12, 12))
    fig.suptitle(f'Lottery Frequency Analysis for Region {region_code}', fontsize=16)

    most_frequent.plot(kind='bar', ax=axes[0], color='skyblue')
    axes[0].set_title('Top 10 Most Frequent Two-Digit Numbers (Historical)')
    axes[0].set_xlabel('Two-Digit Number')
    axes[0].set_ylabel('Frequency')
    axes[0].tick_params(axis='x', rotation=45)
    axes[0].grid(axis='y', linestyle='--', alpha=0.7)

    least_frequent.plot(kind='bar', ax=axes[1], color='salmon')
    axes[1].set_title('Top 10 Least Frequent Two-Digit Numbers (Historical)')
    axes[1].set_xlabel('Two-Digit Number')
    axes[1].set_ylabel('Frequency')
    axes[1].tick_params(axis='x', rotation=45)
    axes[1].grid(axis='y', linestyle='--', alpha=0.7)

    plt.tight_layout(rect=[0, 0.03, 1, 0.96])
    output_dir = os.path.dirname(output_image_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    plt.savefig(output_image_path)
    plt.close()
    print(f"Frequency analysis image for {region_code} saved to {output_image_path}")

# --- New ML Prediction Functions ---

def prepare_ml_data(df, lag=1):
    """
    Prepares data for ML model.
    Features: presence/absence of each number (00-99) in the last 'lag' draws.
    Target: presence/absence of each number (00-99) in the current draw.
    """
    all_numbers_in_draws = []
    for index, row in df.iterrows():
        draw_numbers = []
        for col in df.columns:
            if col not in ['date', 'province']:
                draw_numbers.append(str(row[col]).zfill(2))
        all_numbers_in_draws.append(draw_numbers)

    # Create a binary matrix for all numbers (00-99) for each draw
    binary_matrix = np.zeros((len(all_numbers_in_draws), 100), dtype=int)
    for i, draw in enumerate(all_numbers_in_draws):
        for num_str in draw:
            binary_matrix[i, int(num_str)] = 1

    X = []
    y = []
    dates = []

    for i in range(lag, len(binary_matrix)):
        # Features are the numbers drawn in the previous 'lag' draws
        features_row = binary_matrix[i-lag:i].flatten()
        X.append(features_row)
        # Target is the numbers drawn in the current draw
        y.append(binary_matrix[i])
        dates.append(df['date'].iloc[i])

    return np.array(X), np.array(y), dates

def train_and_predict_ml(X, y, dates, region_code):
    """
    Trains Logistic Regression models for each number and predicts probabilities for the next draw.
    """
    predicted_probabilities = {}
    all_possible_numbers = [str(i).zfill(2) for i in range(100)]

    # Use the last data point for prediction, and the rest for training
    X_train = X[:-1]
    y_train = y[:-1]
    X_predict = X[-1].reshape(1, -1) # Reshape for single prediction

    if len(X_train) == 0:
        print(f"Not enough data to train ML model for {region_code}. Skipping ML prediction.")
        return None

    for i in range(100): # For each number from 00 to 99
        target_y = y_train[:, i] # Target for this specific number

        # Check if there's enough variance in the target for this number
        if len(np.unique(target_y)) < 2:
            # print(f"Skipping training for number {all_possible_numbers[i]} due to insufficient variance in target.")
            predicted_probabilities[all_possible_numbers[i]] = 0.0 # Assign 0 probability if no variance
            continue

        model = LogisticRegression(solver='liblinear', random_state=42, C=0.1) # C is regularization strength
        model.fit(X_train, target_y)
        
        # Predict probability for the next draw
        prob = model.predict_proba(X_predict)[:, 1][0]
        predicted_probabilities[all_possible_numbers[i]] = prob

    # Sort by probability
    sorted_predictions = sorted(predicted_probabilities.items(), key=lambda item: item[1], reverse=True)
    return sorted_predictions

def display_ml_predictions(sorted_predictions, region_code, output_image_path):
    """
    Displays and saves the top 10 ML-predicted numbers as a bar chart.
    """
    if not sorted_predictions:
        return

    top_10_ml = sorted_predictions[:10]
    numbers = [item[0] for item in top_10_ml]
    probabilities = [item[1] for item in top_10_ml]

    plt.figure(figsize=(10, 6))
    plt.bar(numbers, probabilities, color='lightgreen')
    plt.title(f'ML Predicted Top 10 Numbers for Region {region_code}')
    plt.xlabel('Two-Digit Number')
    plt.ylabel('Predicted Probability')
    plt.xticks(rotation=45)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()

    output_dir = os.path.dirname(output_image_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    plt.savefig(output_image_path)
    plt.close()
    print(f"ML prediction image for {region_code} saved to {output_image_path}")


if __name__ == "__main__":
    script_dir = os.path.dirname(__file__)
    project_root = os.path.abspath(os.path.join(script_dir, os.pardir))
    
    regions = {
        'MB': 'xsmb-2-digits.csv',
        'MN': 'xsmn-2-digits.csv',
        'MT': 'xsmt-2-digits.csv'
    }

    for region_code, filename in regions.items():
        data_file_path = os.path.join(project_root, 'data', filename)
        
        # Paths for frequency analysis plots
        freq_output_image = os.path.join(project_root, 'data', f'frequency_analysis_{region_code}.png')
        
        # Paths for ML prediction results (now images)
        ml_prediction_output_image = os.path.join(project_root, 'data', f'ml_prediction_{region_code}.png')

        if os.path.exists(data_file_path):
            # --- Run Frequency Analysis ---
            frequencies = get_number_frequencies(data_file_path)
            plot_frequencies(frequencies, region_code, freq_output_image)

            # --- Run ML Prediction ---
            df_data = pd.read_csv(data_file_path)
            # Ensure date column is sorted for correct lagging
            df_data['date'] = pd.to_datetime(df_data['date'])
            df_data = df_data.sort_values(by='date').reset_index(drop=True)

            X, y, dates = prepare_ml_data(df_data, lag=1) # Using lag=1 for simplicity

            if X.shape[0] > 1: # Need at least 2 data points for training and 1 for prediction
                sorted_ml_predictions = train_and_predict_ml(X, y, dates, region_code)
                if sorted_ml_predictions:
                    display_ml_predictions(sorted_ml_predictions, region_code, ml_prediction_output_image)
            else:
                print(f"Not enough data points ({X.shape[0]}) for ML prediction for {region_code}. Skipping ML prediction.")

        else:
            print(f"Data file not found for region {region_code}: {data_file_path}. Skipping all analysis for this region.")
