import RPi.GPIO as GPIO
import time
import config
import requests
from datetime import datetime 
import traceback

# GPIO pins
PLANTAS = "plantas"
ARBOLES = "arboles"


RELAY_PLANTAS = 17 
RELAY_ARBOLES = 27

# Humidity sensor
SENSOR_PLANTAS = 23
SENSOR_ARBOLES = 24 
MIN_SENSOR_VALUE = 10000
MAX_SENSOR_VALUE = 100000


device_dict = {
    ARBOLES: {
        "relay_pin": RELAY_ARBOLES, 
        "sensor_pin": SENSOR_ARBOLES,
        "hassio_entity": "sensor.arboles_humidity"
    },
    PLANTAS: {
        "relay_pin": RELAY_PLANTAS, 
        "sensor_pin": SENSOR_PLANTAS,
        "hassio_entity": "sensor.plantas_humidity"
    },
}

HUMIDITY_THRESHOLD = 20 #percent

ON = 'on'
OFF = 'off'
DRY = "dry"
schedule = [
    [PLANTAS, "09:00" , ON], 
    [PLANTAS, "09:29" , OFF], 

    [ARBOLES, "09:30", ON],
    [ARBOLES, "09:59", OFF],

    ["all", "16:23", DRY],
    ["all", "14:00", DRY],

    [PLANTAS, "18:00", ON], 
    [PLANTAS, "18:29", OFF], 

    [ARBOLES, "18:30", ON],
    [ARBOLES, "18:59", OFF],

    ["all", "17:13", DRY],
    ["all", "22:00", DRY],

]

def log(msg):
    timelog = datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
    print(f"[{timelog}] {msg}")

log("Initializing garden scheduler")

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(RELAY_PLANTAS, GPIO.OUT)
GPIO.setup(RELAY_ARBOLES, GPIO.OUT)

# Initialize 
GPIO.output(RELAY_PLANTAS, GPIO.LOW) #Blink relay to see if scripts runs successfully
GPIO.output(RELAY_ARBOLES, GPIO.LOW) 
time.sleep(1)
GPIO.output(RELAY_PLANTAS, GPIO.HIGH) 
GPIO.output(RELAY_ARBOLES, GPIO.HIGH) 

def update_hassio_entity(entity, status): 

    log(f"Updating hassio entity {entity} with {status}")

    r = requests.post(f"http://{config.HASSIO_URL}/api/states/{entity}", 
    headers={
        'Authorization': f"Bearer {config.HASSIO_TOKEN}",
        'Content-Type':'application/json'
    }, 
    json={"state": status, "attributes":   {
        "unit_of_measurement": "%",
        "device_class": "humidity"
    } 
})
    print(f"Response {r.text}")

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

log("Starting garden scheduler loop")
while True:
 
    # update humidity every hour 
    if datetime.now().minute == 0: 
        humidity_sensor = read_stable_value(sensor)
        update_hassio_entity("sensor.plantas_humidity", 30)

    try: 
        #log(get_time()) 
        for event in schedule: 
            device = event[0]
            when = event[1]


            if when == get_time(): 
                status = event[2]

                log (f"Schedule event {device}: {status}")

                if status == DRY:
                    for device in [PLANTAS, ARBOLES]: 
                        relay = device_dict[device]['relay_pin']
                        sensor = device_dict[device]['sensor_pin']
                        hassio_entity = device_dict[device]['hassio_entity']

                        humidity_sensor = read_stable_value(sensor)
                        log(f"Humidity on sensor {device}: {humidity_sensor}")
                        if humidity_sensor < HUMIDITY_THRESHOLD: 
                        
                            notify_slack(f"Detected low humidity ({humidity_sensor}%), watering {device}...")
                            log(f"Detected low humidity, watering {device}...")
                            update_hassio_entity(hassio_entity, humidity_sensor)

                            activate(relay, ON)
                            time.sleep(60*5) # 5 minutes 
                            activate(relay, OFF)  
                            log(f"Finished watering {device}")

                            humidity_sensor = read_stable_value(sensor)
                            update_hassio_entity(hassio_entity, humidity_sensor)
                            log(f"Humidity after watering on sensor {sensor}: {humidity_sensor}")

                else:
                    relay = device_dict[device]['relay_pin']
                    sensor = device_dict[device]['sensor_pin']
                    hassio_entity = device_dict[device]['hassio_entity']

                    # if status is ON, check the weather,
                    # and do not active if it is raining today 
                    if status == ON and is_raining_today(): 
                        log (f"It is raining today, not activating {device}")
                    else:
                        humidity_sensor = read_stable_value(sensor)
                        update_hassio_entity(hassio_entity, humidity_sensor)
                        log(f"Humidity on scheduled watering {device} : {humidity_sensor}")
                            
                        activate(relay, status)

        wait_until_next_second()
    except Exception as e:  
        traceback.print_exc()
        notify_slack(f"An error happened: {e}" )
        log("Exiting scheduler")
        GPIO.cleanup() # this ensures a clean exit
        break
        