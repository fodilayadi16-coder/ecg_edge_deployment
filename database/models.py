# This file defines the database model for storing ECG records using SQLModel. Each record includes patient information, prediction results, and a timestamp.

from sqlmodel import SQLModel, Field
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from sqlalchemy import Column, JSON

class Patient(SQLModel, table=True):
    # Validation: ID must be 3-20 chars, name cannot be empty
    patient_id: str = Field(primary_key=True, min_length=3, max_length=20)
    full_name: str = Field(min_length=1)
    age: int = Field(gt=0, lt=120) 

class ECGRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: str = Field(foreign_key="patient.patient_id")
    prediction: int
    confidence: float
    heart_rate: int
    # Raw ADC samples (JSON array) and reconstructed voltage points for frontend plotting
    adc: Optional[List[int]] = Field(default=None, sa_column=Column(JSON, nullable=True))
    voltage: Optional[List[float]] = Field(default=None, sa_column=Column(JSON, nullable=True))

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone(timedelta(hours=1))))