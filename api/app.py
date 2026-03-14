import os

from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, HTTPException, Security, Depends, status, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
import asyncio

from database.db import engine, init_db
from database.models import Patient
from database.crud import get_patient_history, create_patient, get_patient, get_patient_by_full_name

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
        import warnings

        warnings.warn(
            "Missing required environment variable API_KEY. The server will start, but requests requiring authentication will be rejected. Set API_KEY in .env or the environment before starting the app.",
            UserWarning,
        )
    # Install a small asyncio exception handler to suppress noisy
    # ConnectionResetError tracebacks on Windows (WinError 10054) that
    # occur when clients disconnect abruptly. We preserve the existing
    # handler and restore it on shutdown.
    loop = asyncio.get_event_loop()
    prev_handler = loop.get_exception_handler()

    def _exception_handler(loop, context):
        exc = context.get("exception")
        # Suppress 'An existing connection was forcibly closed by the remote host' on Windows
        if isinstance(exc, ConnectionResetError) and getattr(exc, "winerror", None) == 10054:
            return
        if prev_handler:
            return prev_handler(loop, context)
        # fallback to default handling
        loop.default_exception_handler(context)

    loop.set_exception_handler(_exception_handler)
    yield
    # restore previous handler on shutdown
    try:
        loop.set_exception_handler(prev_handler)
    except Exception:
        pass


# Create the FastAPI app with the lifespan manager
app = FastAPI(title="ECG Real-Time Monitor", lifespan=lifespan)

# CORS: allow frontend origins during development so browsers can preflight requests
_cors_origins = os.getenv("CORS_ORIGINS")
if _cors_origins:
    origins = [o.strip() for o in _cors_origins.split(",") if o.strip()]
else:
    origins = [
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -- Patient Registration Endpoint --

@app.post("/register")
async def register_patient(patient: Patient, _: str = Depends(get_api_key)):
    """
    Register a new patient.
    If patient already exists, return existing record.
    """
    # Normalize user input to avoid duplicates due to casing/spacing differences.
    patient.patient_id = patient.patient_id.strip()
    patient.full_name = patient.full_name.strip()

    existing_by_id = get_patient(engine, patient.patient_id)
    if existing_by_id:
        raise HTTPException(status_code=409, detail="Patient already registered with this ID")

    existing_by_name = get_patient_by_full_name(engine, patient.full_name)
    if existing_by_name:
        raise HTTPException(status_code=409, detail="Patient already registered with this full name")

    created = create_patient(engine, patient)

    return {
        "message": "Patient registered successfully",
        "patient": created
    }


@app.get("/patients/by-name")
async def fetch_patient_by_name(full_name: str, _: str = Depends(get_api_key)):
    normalized_name = full_name.strip()
    if not normalized_name:
        raise HTTPException(status_code=400, detail="Full name is required")

    patient = get_patient_by_full_name(engine, normalized_name)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not registered")

    return patient

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