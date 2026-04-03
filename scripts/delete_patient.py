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

if __name__ == "__main__":
    delete_patient("PAT-001")  # delete whatever patient ID you want to remove (and their ECG history)