import RPi.GPIO as GPIO
import time


RELAY_PLANTAS = 17 
RELAY_ARBOLES = 27

# GPIO pins
PIN = 17

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(PIN, GPIO.OUT)


print(f"Activating pin {PIN}")
GPIO.output(PIN, GPIO.LOW) 
time.sleep(60)
print(f"Disabling pin {PIN}")
GPIO.output(PIN, GPIO.HIGH) 
time.sleep(1)
