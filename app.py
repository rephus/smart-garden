import RPi.GPIO as GPIO
import time
import config
import requests
from datetime import datetime 
import traceback

# GPIO pins
plantas = 17
arboles = 27

# Humidity sensor
SENSOR_PIN = 23
MIN_SENSOR_VALUE = 15000
MAX_SENSOR_VALUE = 100000

HUMIDITY_THRESHOLD = 20 #percent

ON = 'on'
OFF = 'off'
DRY = "dry"
schedule = [
    [plantas, "09:00" , ON], 
    [plantas, "09:29" , OFF], 

    [arboles, "09:30", ON],
    [arboles, "09:59", OFF],

    ["all", "12:00", DRY],
    ["all", "14:00", DRY],

    [plantas, "18:00", ON], 
    [plantas, "18:29", OFF], 

    [arboles, "18:30", ON],
    [arboles, "18:59", OFF],

    ["all", "16:53", DRY],
    ["all", "22:00", DRY],

]

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(plantas, GPIO.OUT)
GPIO.setup(arboles, GPIO.OUT)

# Initialize 
GPIO.output(plantas, GPIO.HIGH) 
GPIO.output(arboles, GPIO.HIGH) 

def log(msg):
    timelog = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S") 
    print(f"[{timelog}] {msg}")

def notify_slack(text):   
    log("Notifiying on Slack")
    #r = requests.post(config.SLACK_URL, json={'text': text})


def is_raining_today(): 

    url = f"https://api.darksky.net/forecast/{config.weather_key}/36.65794,-4.5422482?units=si&exclude=hourly"

    response = requests.get(url).json()
    precip_intensity = response['daily']['data'][0]['precipIntensity']
    log(f"precip_intensity: {precip_intensity}")
    return precip_intensity > 0.5


def rc_time (pin_to_circuit):
    count = 0                                       #Output on the pin for 
    GPIO.setup(pin_to_circuit, GPIO.OUT)
    GPIO.output(pin_to_circuit, GPIO.LOW)
    time.sleep(0.01)                                 #Change the pin back to input
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

def read_stable_value(pin, times=5):
    values = []
    while len(values) < times:
        value = rc_time(pin)
        if value == 0: 
            continue 

        values.append(value) # Number between 0 (light) and 5000 (dark) 

    sensor_value = round(avg(values))
    return calculate_percent(sensor_value)


def get_time(): 
    return datetime.now().strftime("%H:%M")

def wait_until_next_second(): 
    t = datetime.utcnow()
    sleeptime = 60 - (t.second + t.microsecond/1000000.0)
    time.sleep(sleeptime)

def activate(device, status):
    # If 0V is present at the relay pin, the corresponding LED lights up, at a HIGH level the LED goes out.
    GPIO.output(device, GPIO.LOW if status == ON else GPIO.HIGH) 

log("Starting garden scheduler")
while True:
 
    try: 
        #log(get_time()) 
        for event in schedule: 
            device = event[0]
            when = event[1]
            status = event[2]

            if when == get_time(): 
                log (f"Schedule event {device}: {status}")

                if status == DRY:
                    humidity_sensor = read_stable_value(SENSOR_PIN)
                    log(f"Humidity on sensor {SENSOR_PIN}: {humidity_sensor}")
                    if humidity_sensor < HUMIDITY_THRESHOLD: 
                        for device in [plantas, arboles]: 
                            notify_slack(f"Detected low humidity ({humidity_sensor}%), watering {device}...")
                            log(f"Detected low humidity, watering {device}...")
                            activate(device, "ON")
                            time.sleep(60*5) # 5 minutes 
                            activate(device, "OFF")  
                            log(f"Finished watering {device}")

                else:
                    # if status is ON, check the weather,
                    # and do not active if it is raining today 
                    if status == ON and is_raining_today(): 
                        log (f"It is raining today, not activating {device}")
                    else:
                        activate(device, status)

        wait_until_next_second()
    except Exception as e:  
        traceback.print_exc()
        notify_slack(f"An error happened: {e}" )
        log("Exiting scheduler")
        GPIO.cleanup() # this ensures a clean exit
        break
        