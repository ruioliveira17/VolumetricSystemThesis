import logging
import serial
import threading
import time

from WeightState import weightState

weight_lock = threading.Lock()

logger = logging.getLogger("qubic.weight")

try:
    ser = serial.Serial("/dev/ttyUSB0", 9600, timeout=3)
    logger.info("Weight scale connected successfully")
except Exception:
    ser = None
    logger.exception("Failed to connect to weight scale")

def weight_loop():
    logger.info("Weight thread started")

    while True:
        try: 
            weight = getWeightSerial()

            if weight is not None:
                with weight_lock:
                    weightState.weight = weight

        except Exception:
            logger.exception("Weight reading error")

        time.sleep(0.05)

def getWeightSerial():
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