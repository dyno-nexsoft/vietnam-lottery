import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime
import numpy as np

def get_most_frequent_numbers(file_path):
    """
    Loads a CSV file, calculates the frequency of each two-digit number,
    and returns the top 10 most frequent.
    """
    df = pd.read_csv(file_path)
    all_numbers = pd.Series(dtype=str)
    for col in df.columns:
        if col not in ['date', 'province']:
            all_numbers = pd.concat([all_numbers, df[col].astype(str).str.zfill(2)])
    
    frequency = all_numbers.value_counts()
    return frequency.head(10)

def get_least_recent_numbers(file_path):
    """
    Loads a CSV file and finds the 10 numbers that have not appeared for the longest time.
    """
    df = pd.read_csv(file_path)
    df['date'] = pd.to_datetime(df['date'])
    
    all_possible_numbers = [str(i).zfill(2) for i in range(100)]
    last_appearance = {}

    for number in all_possible_numbers:
        # Find the last date the number appeared in any prize column
        last_date = df[df.isin([int(number)]).any(axis=1)]['date'].max()
        if pd.notna(last_date):
            last_appearance[number] = last_date

    # Create a series with all numbers and their last appearance date
    last_appearance_series = pd.Series(last_appearance).sort_values(ascending=True)
    
    # Calculate days since last appearance
    days_since_appearance = (datetime.now() - last_appearance_series).dt.days
    
    # Return the top 10 numbers that have not appeared for the longest
    return days_since_appearance.nlargest(10)

def plot_combined_analysis(data, title, ylabel, output_filename):
    """
    Plots a combined analysis for all regions on a single figure with subplots.
    """
    regions = list(data.keys())
    fig, axes = plt.subplots(len(regions), 1, figsize=(12, 6 * len(regions)), constrained_layout=True)
    fig.suptitle(title, fontsize=18, weight='bold')

    if len(regions) == 1:
        axes = [axes] # Make it iterable if there's only one region

    colors = plt.cm.viridis(np.linspace(0, 1, 10))

    for i, region in enumerate(regions):
        series_data = data[region]
        if series_data is not None and not series_data.empty:
            series_data.sort_values(ascending=False).plot(kind='bar', ax=axes[i], color=colors)
            axes[i].set_title(f'Region: {region}', fontsize=14)
            axes[i].set_ylabel(ylabel, fontsize=12)
            axes[i].tick_params(axis='x', rotation=45)
            axes[i].grid(axis='y', linestyle='--', alpha=0.7)
        else:
            axes[i].text(0.5, 0.5, 'No data available', ha='center', va='center')
            axes[i].set_title(f'Region: {region}', fontsize=14)

    plt.savefig(output_filename)
    plt.close()
    print(f"Analysis image saved to {output_filename}")

if __name__ == "__main__":
    script_dir = os.path.dirname(__file__)
    project_root = os.path.abspath(os.path.join(script_dir, os.pardir))
    
    regions_files = {
        'MB': 'xsmb-2-digits.csv',
        'MN': 'xsmn-2-digits.csv',
        'MT': 'xsmt-2-digits.csv'
    }

    most_frequent_data = {}
    least_recent_data = {}

    for region_code, filename in regions_files.items():
        data_file_path = os.path.join(project_root, 'data', filename)
        
        if os.path.exists(data_file_path):
            print(f"Analyzing region: {region_code}")
            most_frequent_data[region_code] = get_most_frequent_numbers(data_file_path)
            least_recent_data[region_code] = get_least_recent_numbers(data_file_path)
        else:
            print(f"Data file not found for region {region_code}: {data_file_path}. Skipping analysis.")
            most_frequent_data[region_code] = None
            least_recent_data[region_code] = None

    # Plot and save the combined images
    if any(data is not None for data in most_frequent_data.values()):
        plot_combined_analysis(
            most_frequent_data,
            'Top 10 Most Frequent Numbers by Region',
            'Frequency Count',
            os.path.join(project_root, 'data', 'most_frequent_numbers.png')
        )

    if any(data is not None for data in least_recent_data.values()):
        plot_combined_analysis(
            least_recent_data,
            'Top 10 Least Recent Numbers by Region',
            'Days Since Last Appearance',
            os.path.join(project_root, 'data', 'least_recent_numbers.png')
        )

    print("Analysis complete.")