from flask import Flask, request, render_template, redirect, url_for
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Utility functions to handle data processing
def process_file(filepath):
    # Determine file type and load data accordingly
    if filepath.endswith('.csv'):
        data = pd.read_csv(filepath)
    elif filepath.endswith('.json'):
        data = pd.read_json(filepath)
    else:
        raise ValueError('Unsupported file format')
    return data

def check_data_quality(data):
    # Check if the data covers at least one complete 2-hour window with consistent 2-minute intervals
    data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')
    data = data.set_index('timestamp')
    data = data.resample('2T').mean()
    two_hour_windows = []
    for start_time in data.index:
        end_time = start_time + pd.Timedelta(hours=2)
        window = data[start_time:end_time]
        if len(window) == 61 and window.notna().all().all():
            two_hour_windows.append(window)
    return two_hour_windows

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
    # Save plot to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    # Encode plot to base64 string
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    return img_str

# Routes
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
    two_hour_windows = check_data_quality(data)
    return render_template('data.html', windows=two_hour_windows, filename=filename)

@app.route('/latest/<filename>')
def latest_data(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    data = process_file(filepath)
    two_hour_windows = check_data_quality(data)
    if two_hour_windows:
        latest_window = two_hour_windows[-1]
        min_hr, max_hr, avg_hr = extract_statistics(latest_window)
        plot_url = plot_heartrate(latest_window)
        return render_template('latest.html', min_hr=min_hr, max_hr=max_hr, avg_hr=avg_hr, plot_url=plot_url)
    else:
        return "No valid 2-hour intervals found."

if __name__ == '__main__':
    app.run(debug=True)
