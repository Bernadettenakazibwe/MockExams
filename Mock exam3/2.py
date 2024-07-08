import pandas as pd

# Load the CSV file
data = pd.read_csv('Mock exam3/diabetes_clean.csv')

# Count the number of diabetes patients
num_diabetes_patients = data['Outcome'].value_counts()[1]
print(num_diabetes_patients)
