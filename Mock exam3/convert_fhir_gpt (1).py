import re
import uuid
from fhir.resources.bundle import Bundle, BundleEntry
from fhir.resources.patient import Patient
from fhir.resources.observation import Observation, ObservationComponent
from fhir.resources.identifier import Identifier
from fhir.resources.narrative import Narrative
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
from fhir.resources.reference import Reference
from fhir.resources.quantity import Quantity
from datetime import datetime, timedelta, date
import pandas as pd

loinc_codes = {
    'Pregnancy': ('82810-3', 'Pregnancy', 'mg/dL', 'Laboratory', 'laboratory'),
    'Glucose': ('15074-8', 'Glucose [Moles/volume] in Blood', 'mg/dL', 'Laboratory', 'laboratory'),
    'BloodPressure': ('85354-9', 'Blood pressure panel with all children optional', 'mm[Hg]', "Vital Signs", "vital-signs"),
    'Insulin': ('14749-6', 'Glucose [Moles/volume] in Serum or Plasma', 'mg/dL', 'Laboratory', 'laboratory'),
    'BMI': ('39156-5', 'BMI', 'kg/m3', "Vital Signs", "vital-signs"),
}

billable_dollars = {
    'Pregnancy': 50.0,
    'Glucose': 75.0,
    'BloodPressure': 100.0,
    'Insulin': 80.0,
    'BMI': 90.0,
}

def calculate_bd(age):
    """ This calculates the birth year of a patient """
    year = datetime.now().year - int(age)  # Convert age to int
    return date(year, 1, 1)  # Return a datetime.date object

def convert_table_to_fhir_bundle(index, row):
    pid = str(uuid.uuid4())
    oid = str(uuid.uuid4())
    peid = str(uuid.uuid4())

    fhir_bundle = Bundle(resourceType='Bundle', type='collection', entry=[])
    columns = row.keys()

    patient_identifier = Identifier()
    patient_identifier.system = 'http://fohispital.thd/patient-ids'
    patient_identifier.value = str(index)

    patient_birth_date = calculate_bd(row['Age'])
    print(f"Patient {index} Birth Date: {patient_birth_date}")  # Debug statement

    patient_resource = Patient(
        id=f'Patient-{pid}',
        birthDate=patient_birth_date,
        identifier=[patient_identifier],
        text=Narrative(
            status="generated",
            div="<div xmlns='http://www.w3.org/1999/xhtml'>A patient resource with a narrative.</div>",
        )
    )

    fhir_bundle.entry.append(
        BundleEntry(
            resource=patient_resource,
            fullUrl=f'http://fohispital.thd/{patient_resource.id}'
        )
    )

    for column in columns:
        if column in ['Age', 'Outcome']:
            continue

        print(f"Processing column: {column} for Patient {index}")  # Debug statement

        observation_resource = Observation(
            id=f"observation-{index}-{oid}-{column}",
            status='final',
            category=[CodeableConcept(
                coding=[Coding(system='http://terminology.hl7.org/CodeSystem/observation-category', code=loinc_codes[column][4], display=loinc_codes[column][3])]
            )],
            code=CodeableConcept(
                coding=[Coding(system='http://loinc.org', code=loinc_codes[column][0], display=loinc_codes[column][1])]
            ),
            subject=Reference(reference=f'Patient/{patient_resource.id}'),
            performer=[Reference(reference=f"Practitioner/{peid}")],
            text=Narrative(
                status="generated",
                div="<div xmlns='http://www.w3.org/1999/xhtml'>An observation resource with a narrative.</div>",
            ),
            effectiveDateTime=f"{datetime.utcnow().isoformat()}",
        )

        if column == "BloodPressure":
            observation_resource.component = [
                ObservationComponent(
                    code=CodeableConcept(
                        coding=[
                            Coding(
                                system="http://loinc.org", code="8480-6", display="Systolic Blood Pressure"
                            )
                        ]
                    ),
                    valueQuantity=Quantity(
                        value=row[column] + 40,
                        unit="mmHg",
                        system="http://unitsofmeasure.org",
                        code="mm[Hg]",
                    ),
                ),
                ObservationComponent(
                    code=CodeableConcept(
                        coding=[
                            Coding(
                                system="http://loinc.org", code="8462-4", display="Diastolic Blood Pressure"
                            )
                        ]
                    ),
                    valueQuantity=Quantity(
                        value=row[column],
                        unit="mmHg",
                        system="http://unitsofmeasure.org",
                        code="mm[Hg]",
                    ),
                )
            ]
        else:
            observation_resource.valueQuantity = Quantity(
                value=row[column],
                unit=loinc_codes[column][2],
                system="http://unitsofmeasure.org",
                code=loinc_codes[column][2],
            )

        fhir_bundle.entry.append(
            BundleEntry(
                resource=observation_resource,
                fullUrl=f'http://fohispital.thd/{observation_resource.id}'
            )
        )

    return fhir_bundle

# Test-Example usage with a pandas DataFrame
df = pd.DataFrame({
    'Pregnancy': [6, 7],
    'Glucose': [148, 120],
    'BloodPressure': [72, 80],
    'Insulin': [0, 30],
    'BMI': [33.6, 25.4],
    'Age': [50, 35],
})

# Uncomment to check final code
# df = pd.read_csv('diabetes_clean.csv')

for index, row in df.iterrows():
    with open(f"{index}.json", 'w') as file:
        fhir_bundle = convert_table_to_fhir_bundle(index, row)
        print(fhir_bundle.json(indent=2))
        file.write(fhir_bundle.json(indent=2))
