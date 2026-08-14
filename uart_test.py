import serial
import time

# Open UART
ser = serial.Serial(
    port="/dev/serial0",   # or /dev/ttyAMA0 depending on your Pi
    baudrate=115200,
    timeout=1
)

time.sleep(2)  # Give UART time to initialize

while True:
    num = input("Enter a number (0-9): ")

    if len(num) == 1 and num.isdigit():
        ser.write(num.encode())
        print(f"Sent: {num}")
    else:
        print("Please enter a single digit.")