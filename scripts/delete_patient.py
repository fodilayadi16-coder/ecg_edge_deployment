from sqlmodel import Session, select
from database.db import engine
from database.models import Patient, ECGRecord

def delete_patient(patient_id: str):
    with Session(engine) as session:
        # delete ECG records
        recs = session.exec(select(ECGRecord).where(ECGRecord.patient_id == patient_id)).all()
        for r in recs:
            session.delete(r)
        # delete patient
        p = session.exec(select(Patient).where(Patient.patient_id == patient_id)).first()
        if p:
            session.delete(p)
        session.commit()
        print("deleted", len(recs), "records and patient", patient_id)

def delete_all():
    """Delete all ECGRecord and Patient rows from the database."""
    with Session(engine) as session:
        recs = session.exec(select(ECGRecord)).all()
        patients = session.exec(select(Patient)).all()
        for r in recs:
            session.delete(r)
        for p in patients:
            session.delete(p)
        session.commit()
        print("deleted", len(recs), "ECG records and", len(patients), "patients")

if __name__ == "__main__":
    # WARNING: This will erase all patient and ECG records from the database.
    delete_all()