import pandas as pd

# Load the CSV file
data = pd.read_csv('Mock exam3/diabetes_clean.csv')

# Billable amounts per observation
billable_amounts = {
    'Pregnancies': 50.0,
    'Glucose': 75.0,
    'BloodPressure': 100.0,
    'Insulin': 80.0,
    'BMI': 90.0
    # 'DiabetesPedigreeFunction' is not in your dataset, so it is excluded
}

# Calculate the total billable amount
total_bill = sum(data[column] * amount for column, amount in billable_amounts.items())

# Get the overall amount
overall_amount = total_bill.sum()
print(overall_amount)
