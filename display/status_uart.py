import serial
import time

PORT = "/dev/serial0"
BAUD = 115200

ser = None


def init_uart():
    global ser

    if ser is None:
        ser = serial.Serial(
            PORT,
            BAUD,
            timeout=1
        )
        time.sleep(2)


def send_status(number):
    global ser

    try:
        init_uart()

        print(f"Sending: {number}")

        ser.write(f"{number}\n".encode())
        ser.flush()          # Make sure it is sent immediately

    except Exception as e:
        print("UART Error:", e)