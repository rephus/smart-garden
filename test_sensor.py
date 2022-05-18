
# include RPi libraries in to Python code
import RPi.GPIO as GPIO
import time

SENSOR_PIN = 24 # 24
MIN_SENSOR_VALUE = 10000
MAX_SENSOR_VALUE = 100000

# instantiate GPIO as an object
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

def rc_time (pin_to_circuit):
    count = 0                                       #Output on the pin for 
    GPIO.setup(pin_to_circuit, GPIO.OUT)
    GPIO.output(pin_to_circuit, GPIO.LOW)
    time.sleep(0.1)                                 #Change the pin back to input
    GPIO.setup(pin_to_circuit, GPIO.IN)             #Count until the pin goes high
    while (GPIO.input(pin_to_circuit) == GPIO.LOW) and count < MAX_SENSOR_VALUE:
        count += 1
    return count                                   #Catch when script is interupted, cleanup correctly

def avg(lst):
    return sum(lst) / len(lst)

def calculate_percent(sensor_value): 
    percent = (sensor_value - MIN_SENSOR_VALUE ) / (MAX_SENSOR_VALUE- MIN_SENSOR_VALUE)
    percent = round(percent,2)
    percent = max(percent * 100 , 0)
    return percent 

def read_stable_value(pin, times):
    values = []
    while len(values) < times:
        value = rc_time(pin)
        if value == 0: 
            continue 

        values.append(value) # Number between 0 (light) and 5000 (dark) 

    sensor_value = round(avg(values))
    return calculate_percent(sensor_value)


try:                                                 # Main loop
    while True:
        sensor_value = rc_time(SENSOR_PIN)
        print ( f"Raw reading: {sensor_value}")

        percent = read_stable_value(SENSOR_PIN, 5)
        print ( f"Percent reading: {percent}%")


except KeyboardInterrupt:
    pass
finally:
    GPIO.cleanup()