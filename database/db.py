# This file contains the database setup and initialization code for the ECG results application.

from sqlmodel import create_engine, SQLModel

sqlite_file_name = "ecg_results.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=False)

def init_db():
    SQLModel.metadata.create_all(engine) # handles Patient and ECGRecord automatically (no manual table definition needed)


# This design is good because it is easy to switch to a different database in the future (like PostgreSQL).