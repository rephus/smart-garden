token="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiI1NzkyYWQ5OWI1MGQ0NmViYmZkMTcxODkzNWVhMDNlMCIsImlhdCI6MTY0MjYwMTk5MCwiZXhwIjoxOTU3OTYxOTkwfQ.FwW4qvwU8UA2gP-YbSvXlj5JS6GbYujAtbV5uhqEqhM"

curl -X POST \
  -H "Authorization: Bearer $token" \
  -H "Content-Type: application/json" \
  -d '{"state": "off", "attributes": {"device_class": "switch" }}' \
  http://192.168.2.126:8123/api/states/sensor.arboles_watering


