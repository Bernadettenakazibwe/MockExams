import os
import pydicom
from datetime import datetime
from flask import Flask, render_template, send_from_directory, Response  # Import Response from Flask
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import io

app = Flask(__name__)

# Define the folder where DICOM files are stored
DICOM_FOLDER = 'mockexam2/dicom'

@app.route('/')
def index():
    image_info = []

    # Iterate through DICOM files in the folder
    for filename in os.listdir(DICOM_FOLDER):
        if filename.endswith('.dcm'):
            filepath = os.path.join(DICOM_FOLDER, filename)
            ds = pydicom.dcmread(filepath)
            
            # Extract metadata
            patient_id = ds.PatientID
            study_date = ds.StudyDate
            age = ds.PatientAge

            # Format age as human readable (remove 'Y' from age)
            age = age[:-1]

            # Format date as human readable
            study_date = datetime.strptime(study_date, '%Y%m%d').strftime('%B %d, %Y %H:%M')

            # Append information to the list
            image_info.append({
                'filepath': filepath,
                'patient_id': patient_id,
                'study_date': study_date,
                'age': age
            })

    # Render HTML template with image_info
    return render_template('index.html', image_info=image_info)

# Route to serve DICOM images
@app.route('/dicom/<path:filename>')
def serve_dicom(filename):
    return send_from_directory(DICOM_FOLDER, filename)

# Route to render DICOM images as PNG
@app.route('/render_image/<path:filename>')
def render_image(filename):
    filepath = os.path.join(DICOM_FOLDER, filename)
    ds = pydicom.dcmread(filepath)

    # Render DICOM image using matplotlib
    fig, ax = plt.subplots()
    ax.imshow(ds.pixel_array, cmap='gray')
    ax.axis('off')  # Hide axis
    plt.tight_layout()

    # Convert plot to PNG image
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    plt.close(fig)

    # Return PNG image data using Response
    return Response(output.getvalue(), mimetype='image/png')

# Route to filter images by patient_id
@app.route('/patient/<patient_id>')
def patient_images(patient_id):
    image_info = []

    # Iterate through DICOM files in the folder
    for filename in os.listdir(DICOM_FOLDER):
        if filename.endswith('.dcm'):
            filepath = os.path.join(DICOM_FOLDER, filename)
            ds = pydicom.dcmread(filepath)
            
            # Extract metadata
            file_patient_id = ds.PatientID

            # Check if current file's patient_id matches requested patient_id
            if file_patient_id == patient_id:
                study_date = ds.StudyDate
                age = ds.PatientAge

                # Format age as human readable (remove 'Y' from age)
                age = age[:-1]

                # Format date as human readable
                study_date = datetime.strptime(study_date, '%Y%m%d').strftime('%B %d, %Y %H:%M')

                # Append information to the list
                image_info.append({
                    'filepath': filepath,
                    'patient_id': patient_id,
                    'study_date': study_date,
                    'age': age
                })

    # Render HTML template with filtered image_info
    return render_template('patient.html', image_info=image_info)

if __name__ == '__main__':
    app.run(debug=True)
