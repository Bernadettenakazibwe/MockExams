from flask import Flask, request, render_template, redirect, url_for
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
import os
import json

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def process_file(filepath):
    try:
        if filepath.endswith('.csv'):
            data = pd.read_csv(filepath)
        elif filepath.endswith('.json'):
            with open(filepath) as f:
                data = json.load(f)

            # Add debug print to check the structure of the JSON data
            print("JSON Data Structure:", data)

            if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                heart_rate_data = []
                for entry in data:
                    if 'heartRateValues' in entry:
                        heart_rates = entry['heartRateValues']
                        for hr in heart_rates:
                            # Ensure hr is a list with two elements
                            if isinstance(hr, list) and len(hr) == 2:
                                timestamp, value = hr
                                heart_rate_data.append({'timestamp': timestamp, 'heartrate': value})
                            else:
                                raise ValueError("Each heart rate entry must be a list with two elements (timestamp and value).")
                    else:
                        raise ValueError("The key 'heartRateValues' is missing in one or more entries of the JSON file.")
                heart_rate_df = pd.DataFrame(heart_rate_data)
                heart_rate_df['timestamp'] = pd.to_datetime(heart_rate_df['timestamp'], unit='ms')
                return heart_rate_df
            else:
                raise ValueError("Unsupported JSON structure.")
        else:
            raise ValueError('Unsupported file format')

        print("Columns in the file:", data.columns.tolist())

        # Handle potential unnamed index column
        if 'Unnamed: 0' in data.columns:
            data.rename(columns={'Unnamed: 0': 'timestamp'}, inplace=True)

        # Check for common timestamp columns
        timestamp_cols = ['timestamp', 'startTimestampGMT', 'endTimestampGMT', 'startTimestampLocal', 'endTimestampLocal']
        timestamp_col = None
        for col in timestamp_cols:
            if col in data.columns:
                timestamp_col = col
                break

        if timestamp_col is None:
            raise KeyError("The required 'timestamp' column is missing.")

        # Ensure timestamp column is in datetime format
        data[timestamp_col] = pd.to_datetime(data[timestamp_col])
        data.rename(columns={timestamp_col: 'timestamp'}, inplace=True)

        return data
    except Exception as e:
        print(f"Error processing file: {e}")
        return None



def check_data_quality(data):
    try:
        data = data.set_index('timestamp')
        data = data.resample('2T').mean()

        two_hour_windows = []
        for start_time in data.index:
            end_time = start_time + pd.Timedelta(hours=2)
            window = data[start_time:end_time]
            if len(window) == 61 and window.notna().all().all():
                two_hour_windows.append(window)

        return two_hour_windows
    except Exception as e:
        print(f"Error checking data quality: {e}")
        return []

def extract_statistics(window):
    min_hr = window['heartrate'].min()
    max_hr = window['heartrate'].max()
    avg_hr = window['heartrate'].mean()
    return min_hr, max_hr, avg_hr

def plot_heartrate(window):
    plt.figure(figsize=(10, 5))
    plt.plot(window.index, window['heartrate'], marker='o')
    plt.title('Heart Rate Over Time')
    plt.xlabel('Time')
    plt.ylabel('Heart Rate')
    plt.grid(True)
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    return img_str

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            return redirect(url_for('process_data', filename=file.filename))
    return render_template('upload.html')

@app.route('/process/<filename>')
def process_data(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    data = process_file(filepath)
    if data is not None:
        two_hour_windows = check_data_quality(data)
        return render_template('data.html', windows=two_hour_windows, filename=filename)
    else:
        return "Error processing file. Please check the file format and contents."

@app.route('/latest/<filename>')
def latest_data(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    data = process_file(filepath)
    if data is not None:
        two_hour_windows = check_data_quality(data)
        if two_hour_windows:
            latest_window = two_hour_windows[-1]
            min_hr, max_hr, avg_hr = extract_statistics(latest_window)
            plot_url = plot_heartrate(latest_window)
            return render_template('latest.html', min_hr=min_hr, max_hr=max_hr, avg_hr=avg_hr, plot_url=plot_url)
        else:
            return "No valid 2-hour intervals found."
    else:
        return "Error processing file. Please check the file format and contents."

if __name__ == '__main__':
    app.run(debug=True)
