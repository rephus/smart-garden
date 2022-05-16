import RPi.GPIO as GPIO
import time
import config
import requests
from datetime import datetime 

# GPIO pins
plantas = 1 
arboles = 2

ON = 'on'
OFF = 'off'

schedule = [
    [plantas, "09:00" , ON], 
    [plantas, "09:29" , OFF], 

    [arboles, "09:00", ON],
    [arboles, "09:59", OFF],

    [plantas, "18:00", ON], 
    [plantas, "18:29", OFF], 

    [arboles, "18:30", ON],
    [arboles, "18:59", OFF]
]

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(plantas, GPIO.OUT)
GPIO.setup(arboles, GPIO.OUT)

def log(msg):
    timelog = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S") 
    print(f"[{timelog}] {msg}")

def is_raining_today(): 

    url = f"https://api.darksky.net/forecast/{config.weather_key}/36.65794,-4.5422482?units=si&exclude=hourly"

    response = requests.get(url).json()
    precip_intensity = response['daily']['data'][0]['precipIntensity']
    log(f"is_raining_today > precip_intensity: {precip_intensity}")
    return precip_intensity > 0.5

def get_time(): 
    return datetime.now().strftime("%H:%M")

def wait_until_next_second(): 
    t = datetime.utcnow()
    sleeptime = 60 - (t.second + t.microsecond/1000000.0)
    time.sleep(sleeptime)

def activate(device, status):
    log (f"{get_time()} Schedule event {device}: {status}")

    # if status is ON, check the weather,
    # and do not active if it is raining today 
    if status == ON and is_raining_today(): 
        log (f"{get_time()} It is raining today, not activating {device}")
        return

    GPIO.output(device, GPIO.HIGH if status == ON else GPIO.LOW) 

while True:
 
    log(get_time()) 
    for event in schedule: 
        device = event[0]
        when = event[1]
        status = event[2]

        if when == get_time(): 
            activate(device, status)

    wait_until_next_second()
