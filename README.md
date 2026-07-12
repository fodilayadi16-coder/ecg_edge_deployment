# ECG Edge Deployment

Using synthetic ECG for testing the working of our system before moving to ESP32 data acquisition from AD8232 sensor.

Project for running ECG inference at the edge and managing patient records.

## Overview
- `api/` — FastAPI and websocket utilities
- `database/` — DB models and CRUD helpers
- `inference/` — model prediction code and timing helpers
- `preprocessing/`, `signal_processing/`, `signal_source/` — signal handling and generators
- `model/` — contains the TFLite model used for inference

