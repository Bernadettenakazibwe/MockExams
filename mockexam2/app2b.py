import os
import pydicom
from datetime import datetime
from flask import Flask, jsonify, send_from_directory
from fhirclient.models import imagingstudy as fhir_imagingstudy
from fhirclient.models import fhirreference

app = Flask(__name__)

# Define the folder where DICOM files are stored
DICOM_FOLDER = 'mockexam2/dicom'

# Function to extract DICOM metadata and convert to FHIR resources
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

    # Prepare metadata as FHIR ImagingStudy resource
    imaging_study = fhir_imagingstudy.ImagingStudy()
    imaging_study.subject = {'reference': f'Patient/{patient_id}'}  # Correct way to set FHIRReference
    imaging_study.started = study_date  # Assuming study_date can represent ImagingStudy start date
    # Add more details from DICOM metadata to ImagingStudy

    return imaging_study.as_json()

# Route to serve DICOM metadata for a specific patient as JSON
@app.route('/api/patient/<patient_id>')
def serve_patient_dicom(patient_id):
    metadata_list = []

    # Iterate through DICOM files in the folder
    for filename in os.listdir(DICOM_FOLDER):
        if filename.endswith('.dcm'):
            filepath = os.path.join(DICOM_FOLDER, filename)
            ds = pydicom.dcmread(filepath)
            
            # Check if current file's patient_id matches requested patient_id
            if ds.PatientID == patient_id:
                # Extract metadata and convert to FHIR ImagingStudy resource
                imaging_study_json = extract_dicom_metadata(filepath)
                metadata_list.append(imaging_study_json)

    # Return metadata as JSON response
    return jsonify(metadata_list)

# Route to serve DICOM images
@app.route('/dicom/<path:filename>')
def serve_dicom(filename):
    return send_from_directory(DICOM_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)
