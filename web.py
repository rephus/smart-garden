from flask import Flask
from flask import render_template
from mcp3008 import MCP3008
import RPi.GPIO as GPIO
import requests
import config

RELAY_PLANTAS = 17 
RELAY_ARBOLES = 27

adc = MCP3008()

app = Flask(__name__)

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
#GPIO.setwarnings(False)
GPIO.setup(RELAY_PLANTAS, GPIO.OUT)
GPIO.setup(RELAY_ARBOLES, GPIO.OUT)

def update_hassio_device(entity, status): 
    try: 
        print(f"Updating hassio entity {entity} with {status}")

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
        print(f"Hassio response: {r.text}")
    except Exception as e: 
        print(f"Unable to update hassio entity: {e}")


@app.route("/")
def hello_world():
    return render_template('index.html')


@app.route("/trigger/<device>/<status>")
def trigger(device, status):
    device = int(device) 
    print(f"Triggering device {device} {status}")
    GPIO.output(device, GPIO.LOW if status == "on" else GPIO.HIGH) 

    device_id = 'sensor.arboles_watering' if device == 27 else 'sensor.plantas_watering'
    update_hassio_device(device_id, status)
    return f"device {device} {status}"


@app.route("/sensor/<device>")
def sensor(device):
    device = int(device)
    value = adc.read( channel = device ) # puedes ajustar el canal en el que lees
    n = value / 1023.0 * 3.3 # I assume the value is something between 0 and 1 , inverted
    percent_value = 100 - int(n * 100)
    print(f"Reading sensor {device}: {percent_value}")

    return f"{percent_value}"
