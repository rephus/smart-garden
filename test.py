import RPi.GPIO as GPIO
import time

# GPIO pins
PIN_1 = 17
PIN_2 = 27

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(PIN_1, GPIO.OUT)
GPIO.setup(PIN_2, GPIO.OUT)


print(f"Activating pin {PIN_1}")
GPIO.output(PIN_1, GPIO.LOW) 
time.sleep(3)
print(f"Disabling pin {PIN_1}")
GPIO.output(PIN_1, GPIO.HIGH) 
time.sleep(3)
print(f"Activating pin {PIN_2}")
GPIO.output(PIN_2, GPIO.LOW) 
time.sleep(3)
print(f"Disabling pin {PIN_2}")
GPIO.output(PIN_2, GPIO.HIGH) 
time.sleep(3)