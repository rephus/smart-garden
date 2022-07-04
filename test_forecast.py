import config
import requests

url = f"https://api.darksky.net/forecast/{config.weather_key}/36.65794,-4.5422482?units=si&exclude=hourly"

response = requests.get(url,timeout=10)
print(f"Response: {response}")
print(f"Response status code: {response.status_code}")

response_json = response.json()

precip_intensity = response_json['daily']['data'][0]['precipIntensity']
print(f"precip_intensity: {precip_intensity}")
