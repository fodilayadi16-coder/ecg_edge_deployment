import os

from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, HTTPException, Security, Depends, status, WebSocketDisconnect
from fastapi.security import APIKeyHeader

from database.db import engine, init_db
from database.models import Patient
from database.crud import get_patient_history, create_patient, get_patient

from api.broadcast import add_connection, remove_connection


# Load environment variables from .env if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# -- Authentication Configuration --

# Read API key from environment (no hardcoded default). A .env file
# will be loaded above if python-dotenv is available.
API_KEY = os.getenv("API_KEY")
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

async def get_api_key(header_key: str = Security(api_key_header)):
    """Validates the API Key provided in the request headers."""
    if header_key == API_KEY:
        return header_key
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API Key",
    )

# -- Lifespan (startup/shutdown) --


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if not API_KEY:
        raise RuntimeError(
            "Missing required environment variable API_KEY. Set it in .env or the environment before starting the app."
        )
    yield


# Create the FastAPI app with the lifespan manager
app = FastAPI(title="ECG Real-Time Monitor", lifespan=lifespan)

# -- Patient Registration Endpoint --

@app.post("/register")
async def register_patient(patient: Patient, _: str = Depends(get_api_key)):
    """
    Register a new patient.
    If patient already exists, return existing record.
    """
    existing = get_patient(engine, patient.patient_id)

    if existing:
        return {
            "message": "Patient already exists",
            "patient": existing
        }

    created = create_patient(engine, patient)

    return {
        "message": "Patient registered successfully",
        "patient": created
    }

# -- History Endpoint --

@app.get("/history/{patient_id}")
async def fetch_history(patient_id: str, limit: int = 20):
    history = get_patient_history(engine, patient_id, limit)
    if not history:
        raise HTTPException(status_code=404, detail="No history found for this patient")
    return history

# -- WebSocket Endpoint (ECG Streaming) --

@app.websocket("/ws/{patient_id}")
async def websocket_predict(websocket: WebSocket, patient_id: str):
    # Check API key token in query params (browsers can't set custom headers easily)
    token = websocket.query_params.get("token")
    if token != API_KEY:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()

    # Fetch patient info (optional)
    patient = get_patient(engine, patient_id)

    if not patient:
        await websocket.send_json({"error": "Patient not found"})
        await websocket.close()
        return

    full_name = patient.full_name
    age = patient.age

    # Register this websocket with the broadcast module and wait for disconnects
    await add_connection(patient_id, websocket, full_name, age)

    try:
        # Keep the socket open; the producer will broadcast messages to registered sockets
        while True:
            try:
                await websocket.receive_text()
            except WebSocketDisconnect:
                break
    finally:
        await remove_connection(patient_id, websocket)
        try:
            await websocket.close()
        except Exception:
            pass