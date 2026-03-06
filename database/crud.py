# This file contains functions to interact with the data so your app.py doesn't have to deal with raw session logic.

from sqlmodel import Session, select
from .models import Patient, ECGRecord

# Patient CRUD

def create_patient(engine, patient: Patient):
    """
    Create or register a new patient.
    """
    with Session(engine) as session:
        session.add(patient)
        session.commit()
        session.refresh(patient)
        return patient


def get_patient(engine, patient_id: str):
    """
    Retrieve a patient by ID.
    Returns None if not found.
    """
    with Session(engine) as session:
        statement = select(Patient).where(Patient.patient_id == patient_id)
        return session.exec(statement).first()

# ECG Record CRUD

def create_ecg_record(engine, record: ECGRecord):
    """
    Save an ECG record to database.
    """
    with Session(engine) as session:
        session.add(record)
        session.commit()
        session.refresh(record)
        return record


def get_patient_history(engine, patient_id: str, limit: int = 100):
    """
    Get ECG history for a patient.
    """
    with Session(engine) as session:
        statement = (
            select(ECGRecord)
            .where(ECGRecord.patient_id == patient_id)
            .order_by(ECGRecord.timestamp.desc())
            .limit(limit)
        )
        return session.exec(statement).all()