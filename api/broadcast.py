import asyncio
import logging
import time
from collections import deque, defaultdict
from typing import Set, Dict, List

import numpy as np
from fastapi import WebSocket

from signal_source.synthetic_ecg import generate_ecg_stream
from preprocessing.preprocess import preprocess_window
from api.deps import predictor
from signal_processing.heart_rate import estimate_hr, smooth_bpm
from database.crud import create_ecg_record
from database.db import engine
from database.models import ECGRecord
from datetime import datetime

logger = logging.getLogger("ecg.broadcast")

# Constants (keep in sync with app.py)
SAMPLING_RATE = 360
WINDOW_SIZE = 360
HR_BUFFER_SECONDS = 5
HR_BUFFER_SIZE = SAMPLING_RATE * HR_BUFFER_SECONDS

# Registry: patient_id -> set of WebSocket
connections: Dict[str, Set[WebSocket]] = defaultdict(set)
# background producer tasks per patient
producer_tasks: Dict[str, asyncio.Task] = {}


async def add_connection(patient_id: str, websocket: WebSocket, full_name: str, age: int):
    """Register a websocket and ensure a producer is running for this patient."""
    connections[patient_id].add(websocket)
    logger.info("Connection added for patient %s (total=%d)", patient_id, len(connections[patient_id]))
    if patient_id not in producer_tasks:
        logger.info("Starting producer for patient %s", patient_id)
        producer_tasks[patient_id] = asyncio.create_task(_patient_producer(patient_id, full_name, age))


async def remove_connection(patient_id: str, websocket: WebSocket):
    """Unregister a websocket and cancel producer if no clients remain."""
    connections[patient_id].discard(websocket)
    logger.info("Connection removed for patient %s (remaining=%d)", patient_id, len(connections.get(patient_id, [])))
    if not connections[patient_id]:
        task = producer_tasks.pop(patient_id, None)
        if task:
            logger.info("Cancelling producer for patient %s because no clients remain", patient_id)
            task.cancel()


async def _patient_producer(patient_id: str, full_name: str, age: int):
    """Single producer per patient: reads a stream, does inference and broadcasts to all listeners."""
    stream = generate_ecg_stream(sampling_rate=SAMPLING_RATE)
    hr_signal_buffer = deque(maxlen=HR_BUFFER_SIZE)
    window_duration = WINDOW_SIZE / SAMPLING_RATE

    try:
        logger.info("Producer running for patient %s", patient_id)
        while connections.get(patient_id):
            window = []
            for _ in range(WINDOW_SIZE):
                try:
                    sample = next(stream)
                except StopIteration:
                    logger.warning("ECG stream ended for patient %s", patient_id)
                    return
                window.append(sample)
                hr_signal_buffer.append(sample)

            window_np = np.array(window)

            loop_t0 = time.perf_counter()

            processed = await asyncio.to_thread(preprocess_window, window_np)
            output = await asyncio.to_thread(predictor.predict, processed)

            predicted_class = int(np.argmax(output))
            confidence = float(np.max(output))

            hr_buffer_np = np.array(hr_signal_buffer)
            raw_bpm = estimate_hr(hr_buffer_np, fs=SAMPLING_RATE)
            bpm = smooth_bpm(raw_bpm)

            # Convert ADC counts to a reconstructed ECG voltage-like signal for storage and frontend plotting
            # synthetic_ecg encodes adc = (ecg * 200) + 2048 so we reverse that here
            voltage_points = ((window_np.astype(float) - 2048.0) / 200.0).round(4).tolist()
            adc_samples = window_np.astype(int).tolist()

            new_record = ECGRecord(
                patient_id=patient_id,
                prediction=predicted_class,
                confidence=confidence,
                heart_rate=int(bpm),
                adc=adc_samples,
                voltage=voltage_points
            )

            created_record = None
            try:
                created_record = await asyncio.to_thread(create_ecg_record, engine, new_record)
            except Exception as db_err:
                logger.exception("DB save failed for patient %s: %s", patient_id, db_err)

            total_proc_time = time.perf_counter() - loop_t0

            timestamp = created_record.timestamp.isoformat() if created_record is not None else datetime.utcnow().isoformat()

            payload = {
                "patient_id": patient_id,
                "full_name": full_name,
                "age": age,
                "prediction": predicted_class,
                "confidence": round(confidence, 4),
                "heart_rate": int(bpm),
                "timestamp": timestamp,
                "voltage": voltage_points,
                "adc": adc_samples,
                "processing_time": f"{total_proc_time:.3f}s"
            }

            # Broadcast to all connections for this patient
            ws_list: List[WebSocket] = list(connections.get(patient_id, set()))
            send_coros = [_safe_send(ws, payload) for ws in ws_list]

            if send_coros:
                results = await asyncio.gather(*send_coros, return_exceptions=True)
                # prune failed connections
                for ws, res in zip(ws_list, results):
                    if isinstance(res, Exception):
                        logger.warning("Removing websocket for patient %s due to send error: %s", patient_id, res)
                        try:
                            await ws.close()
                        except Exception:
                            pass
                        connections[patient_id].discard(ws)

            remaining = window_duration - total_proc_time
            if remaining > 0:
                await asyncio.sleep(remaining)

    except asyncio.CancelledError:
        logger.info("Producer cancelled for patient %s", patient_id)
        return
    except Exception as e:
        logger.exception("Producer error for %s: %s", patient_id, e)
    finally:
        connections.pop(patient_id, None)
        producer_tasks.pop(patient_id, None)


async def _safe_send(ws: WebSocket, payload: dict):
    try:
        # send with a short timeout to avoid slow clients stalling the producer
        await asyncio.wait_for(ws.send_json(payload), timeout=2.0)
    except Exception as e:
        logger.debug("Send failed to websocket: %s", e)
        return e
