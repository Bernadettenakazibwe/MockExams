import pandas as pd

# Load the CSV file
data = pd.read_csv('Mock exam3/diabetes_clean.csv')

# Calculate the number of diabetes patients
num_diabetes_patients = data[data['Outcome'] == 1].shape[0]

# Average annual cost per diabetes patient
average_cost_per_patient = 9600

# Calculate the total cost for all diabetes patients
total_cost = num_diabetes_patients * average_cost_per_patient
print(total_cost)
