import RPi.GPIO as GPIO
import time
import config
import requests
from datetime import datetime 
import traceback
from mcp3008 import MCP3008

# GPIO pins
PLANTAS = "plantas"
ARBOLES = "arboles"


RELAY_PLANTAS = 17 
RELAY_ARBOLES = 27

# Humidity sensor
SENSOR_PLANTAS = 0 # channel in MCP3008
SENSOR_ARBOLES = 1 
MIN_SENSOR_VALUE = 10000
MAX_SENSOR_VALUE = 100000


device_dict = {
    ARBOLES: {
        "relay_pin": RELAY_ARBOLES, 
        "sensor_pin": SENSOR_ARBOLES,
        "hassio_entity": "sensor.arboles_humidity",
        "hassio_watering": "sensor.arboles_watering"
    },
    PLANTAS: {
        "relay_pin": RELAY_PLANTAS, 
        "sensor_pin": SENSOR_PLANTAS,
        "hassio_entity": "sensor.plantas_humidity",
        "hassio_watering": "sensor.plantas_watering"
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

    ["all", "11:05", DRY], #water each devide for 5 minutes if sensor is below threshold
    ["all", "14:00", DRY],

    [PLANTAS, "16:05", ON], 
    [PLANTAS, "16:29", OFF], 

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
#GPIO.setwarnings(False)
GPIO.setup(RELAY_PLANTAS, GPIO.OUT)
GPIO.setup(RELAY_ARBOLES, GPIO.OUT)

# Initialize 
GPIO.output(RELAY_PLANTAS, GPIO.LOW) #Blink relay to see if scripts runs successfully
GPIO.output(RELAY_ARBOLES, GPIO.LOW) 
time.sleep(1)
GPIO.output(RELAY_PLANTAS, GPIO.HIGH) 
GPIO.output(RELAY_ARBOLES, GPIO.HIGH) 

adc = MCP3008()

def update_hassio_device(entity, status): 
    try: 
        log(f"Updating hassio entity {entity} with {status}")

        r = requests.post(f"http://{config.HASSIO_URL}/api/states/{entity}", 
            timeout=10,
                headers={
                'Authorization': f"Bearer {config.HASSIO_TOKEN}",
                'Content-Type':'application/json'
            }, 
            json={"state": status, 
                "attributes":   {
                "device_class": "switch"
            } 
        })
        log(f"Hassio response: {r.text}")
    except Exception as e: 
        log(f"Unable to update hassio entity: {e}")

def update_hassio_humidity(entity, status): 
    try: 
        log(f"Updating hassio entity {entity} with {status}")

        r = requests.post(f"http://{config.HASSIO_URL}/api/states/{entity}", 
            timeout=10,
                headers={
                'Authorization': f"Bearer {config.HASSIO_TOKEN}",
                'Content-Type':'application/json'
            }, 
            json={"state": status, 
                "attributes":   {
                "unit_of_measurement": "%",
                "device_class": "humidity"
            } 
        })
        log(f"Hassio response: {r.text}")
    except Exception as e: 
        log(f"Unable to update hassio entity: {e}")


def notify_slack(text):   
    try: 

        log("Notifiying on Slack")
        r = requests.post(config.SLACK_URL, json={'text': text, "icon_emoji": "sweat_drops", "username": "Smart garden"},timeout=10)
        log(f"Slack response: {r.text}")
    except Exception as e: 
        log(f"Unable to send message to slack: {e}")

def is_raining_today(): 
    try: 
        url = f"https://api.darksky.net/forecast/{config.weather_key}/36.65794,-4.5422482?units=si&exclude=hourly"

        response = requests.get(url,timeout=10)
        if response.status_code < 300:

            response_json = response.json()

            precip_intensity = response_json['daily']['data'][0]['precipIntensity']
            log(f"precip_intensity: {precip_intensity}")
            return precip_intensity > 0.5
        else: 
            msg = f"Error fetching darksky weather {response.text}"
            log(msg)
            notify_slack(msg)
            return False 
    except Exception as e: 
        log(f"Unable to get darsky weather : {e}")
        return False 


#deprecated 
def calculate_percent(sensor_value): 
    percent = (sensor_value - MIN_SENSOR_VALUE ) / (MAX_SENSOR_VALUE- MIN_SENSOR_VALUE)
    percent = round(percent,2)
    percent = max(percent * 100 , 0)
    return percent 


def read_sensor(pin): 

    value = adc.read( channel = pin )
    n = value / 1023.0 * 3.3 # I assume the value is something between 0 and 1 , inverted
    percent_value = 100 - (n * 100)
    log(f"Humidity sensor value {n}: {percent_value}")
    return percent_value

def get_time(): 
    return datetime.now().strftime("%H:%M")

def wait_until_next_second(): 
    t = datetime.utcnow()
    sleeptime = 60 - (t.second + t.microsecond/1000000.0)
    time.sleep(sleeptime)

def activate(device, status):
    # If 0V is present at the relay pin, the corresponding LED lights up, at a HIGH level the LED goes out.
    GPIO.output(device, GPIO.LOW if status == ON else GPIO.HIGH) 

# On restart, network is unreachable, so no point doing this at the beggining
if False: 
    for device in [PLANTAS, ARBOLES]: 
        try: 
            sensor = device_dict[device]['sensor_pin']
            hassio_entity = device_dict[device]['hassio_entity']
            humidity_sensor = read_sensor(sensor)
            log(f"Humidity on sensor {device}: {humidity_sensor}")
            update_hassio_humidity(hassio_entity, humidity_sensor)
        except Exception as e: 
            log(f"Error when updating humidity sensor on start: {e}")

log("Starting garden scheduler loop")
while True:
    try: 
        # update humidity every hour 
        if datetime.now().minute == 0: 
            log("Periodic humidity check on sensors")
            for device in [PLANTAS, ARBOLES]: 
                sensor = device_dict[device]['sensor_pin']
                hassio_entity = device_dict[device]['hassio_entity']
                humidity_sensor = read_sensor(sensor)
                log(f"Humidity on sensor {device}: {humidity_sensor}")
                update_hassio_humidity(hassio_entity, humidity_sensor)

    
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
                        hassio_watering = device_dict[device]['hassio_watering']

                        humidity_sensor = read_sensor(sensor)
                        log(f"Humidity on sensor {device}: {humidity_sensor}")
                        if humidity_sensor < HUMIDITY_THRESHOLD: 
                        
                            notify_slack(f"Detected low humidity ({humidity_sensor}%), watering {device}...")
                            log(f"Detected low humidity, watering {device}...")
                            update_hassio_humidity(hassio_entity, humidity_sensor)
                            update_hassio_device(hassio_watering, "on")

                            activate(relay, ON)
                            time.sleep(60*5) # 5 minutes 
                            activate(relay, OFF)  
                            update_hassio_device(hassio_watering, "off")

                            log(f"Finished watering {device}")

                            humidity_sensor = read_sensor(sensor)
                            log(f"Humidity after watering on sensor {sensor}: {humidity_sensor}")
                            update_hassio_humidity(hassio_entity, humidity_sensor)

                else:
                    relay = device_dict[device]['relay_pin']
                    sensor = device_dict[device]['sensor_pin']
                    hassio_entity = device_dict[device]['hassio_entity']
                    hassio_watering = device_dict[device]['hassio_watering']

                    # if status is ON, check the weather,
                    # and do not active if it is raining today 
                    if status == ON and is_raining_today(): 
                        log (f"It is raining today, not activating {device}")
                    else:
                        humidity_sensor = read_sensor(sensor)
                        update_hassio_humidity(hassio_entity, humidity_sensor)
                        log(f"Humidity on scheduled watering {device} : {humidity_sensor}")

                        update_hassio_device(hassio_watering, status)

                        activate(relay, status)

        wait_until_next_second()
    except Exception as e:  
        traceback.print_exc()
        notify_slack(f"An error happened: {e}" )
        log("Exiting scheduler")
        GPIO.cleanup() # this ensures a clean exit
        break
        