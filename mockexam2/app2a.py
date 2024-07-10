import os
import pydicom
from datetime import datetime
from flask import Flask, jsonify, send_from_directory  # Import necessary modules

app = Flask(__name__)

# Define the folder where DICOM files are stored
DICOM_FOLDER = 'mockexam2/dicom'

# Function to extract DICOM metadata
def extract_dicom_metadata(filepath):
    ds = pydicom.dcmread(filepath)

    # Extract metadata
    patient_id = ds.PatientID
    study_date = ds.StudyDate
    age = ds.PatientAge

    # Format age as human readable (remove 'Y' from age)
    age = age[:-1]

    # Format date as human readable
    study_date = datetime.strptime(study_date, '%Y%m%d').strftime('%B %d, %Y %H:%M')

    # Construct link to image on disk
    image_link = f"/dicom/{os.path.basename(filepath)}"

    # Prepare metadata as dictionary
    metadata = {
        'patient_id': patient_id,
        'study_date': study_date,
        'age': age,
        'image_link': image_link
    }

    return metadata

# Route to serve all DICOM metadata as JSON
@app.route('/api')
def serve_dicom_metadata():
    metadata_list = []

    # Iterate through DICOM files in the folder
    for filename in os.listdir(DICOM_FOLDER):
        if filename.endswith('.dcm'):
            filepath = os.path.join(DICOM_FOLDER, filename)
            metadata = extract_dicom_metadata(filepath)
            metadata_list.append(metadata)

    # Return metadata as JSON response
    return jsonify(metadata_list)

# Route to serve DICOM images
@app.route('/dicom/<path:filename>')
def serve_dicom(filename):
    return send_from_directory(DICOM_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)
