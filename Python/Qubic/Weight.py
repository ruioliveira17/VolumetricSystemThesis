import logging
import serial
import subprocess
import threading
import time

from WeightState import weightState

weight_lock = threading.Lock()
serial_lock = threading.Lock()

weight_stop_event = threading.Event()

logger = logging.getLogger("qubic.weight")

original_tty_settings = None

try:
    result = subprocess.run(
        ["stty", "-F", "/dev/ttyUSB0", "-g"],
        capture_output=True,
        text=True,
        check=True
    )

    original_tty_settings = result.stdout.strip()

    ser = serial.Serial("/dev/ttyUSB0", 9600, timeout=3)
    logger.info("Weight scale connected successfully")
except Exception:
    ser = None
    logger.exception("Failed to connect to weight scale")

def weight_loop():
    logger.info("Weight thread started")

    while not weight_stop_event.is_set():
        try: 
            weight = getWeightSerial()

            if weight is not None:
                with weight_lock:
                    weightState.weight = weight

        except Exception:
            logger.exception("Weight reading error")

        time.sleep(0.05)

    logger.info("Weight thread stopped")

def getWeightSerial():
    with serial_lock:
        value = ser.readline()

    if value:
        value = value.rstrip(b"\r\n")

        if len(value) == 9:
            prefix = chr(value[0])

            if prefix == "P":
                digits = value[1:8].decode("ascii")
                status = value[8]

                flags = {
                    "stable": bool(status & 0x01),
                    "tare": bool(status & 0x02),
                    "zero": bool(status & 0x04),
                    "negative": bool(status & 0x08),
                    "min_weight": bool(status & 0x10),
                    "fixed_tare": bool(status & 0x20),
                    "adc_error": bool(status & 0x40),
                }

                return {
                    "prefix": prefix,
                    "weight": digits,
                    "flags": flags
                }

def zeroWeight():
    if ser is None:
        logger.error("Cannot zero weight: scale is not connected")
        return False

    try:
        with serial_lock:
            command = b"<T20" + b"\x01" + b">"
            ser.write(command)
            time.sleep(0.1)
            ser.flush()

        logger.info("Weight zero command sent successfully")

        return True

    except Exception:
        logger.exception("Failed to send weight zero command")
        return False

def closeWeightSerial():
    global ser

    if ser is None:
        return

    try:
        with serial_lock:
            if ser.is_open:
                ser.close()

            if original_tty_settings:
                subprocess.run(
                    ["stty", "-F", "/dev/ttyUSB0", original_tty_settings],
                    check=True
                )
                
            logger.info("Weight scale serial port closed")
    except Exception:
        logger.exception("Failed to close weight scale serial port")