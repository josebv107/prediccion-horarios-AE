import urllib.request
import urllib.parse
import json

url = "http://localhost:8000/api/predict"
data = {
    "codigo": "000555555",
    "seccion_ids": [],
    "personal_context": {
        "trabaja": 1,
        "horas_trabajo_semana": 48,
        "tiempo_traslado_diario": 60
    }
}

req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode())
        print(json.dumps(result, indent=2))
except Exception as e:
    print("Error:", e)
