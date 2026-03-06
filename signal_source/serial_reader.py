import serial
import time

def generate_ecg_stream(port="/dev/ttyUSB0", baudrate=115200): # if testing on Windows, change port to "COM3" or appropriate COM port
    """
    Reads ECG samples from ESP32 over serial.
    Yields one float sample at a time.
    """

    ser = serial.Serial(port, baudrate, timeout=1)

    # Wait for connection
    time.sleep(2)

    print(f"Connected to {port}")

    while True:
        try:
            line = ser.readline().decode("utf-8").strip()

            if line:
                value = float(line)
                yield value

        except Exception:
            continue