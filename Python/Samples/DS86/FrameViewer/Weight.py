import serial

def getWeight():
    with serial.Serial("/dev/ttyUSB0", 9600, timeout=2) as ser:
        while True:
            value = ser.readline()

            if not value:
                continue

            value = value.rstrip(b"\r\n")

            if len(value) < 9:
                continue

            prefix = chr(value[0])

            if prefix != "P":
                continue

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

if __name__ == "__main__":
    print(getWeight())