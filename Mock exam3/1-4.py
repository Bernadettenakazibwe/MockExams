import pandas as pd

# Load the CSV file
data = pd.read_csv('Mock exam3/diabetes_clean.csv')

# Get the number of records in the dataset
num_records = data.shape[0]
print(num_records)
