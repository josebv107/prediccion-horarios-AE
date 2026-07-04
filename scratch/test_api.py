import urllib.request, json
try:
    resp = urllib.request.urlopen('http://localhost:8000/api/eligible-courses?codigo=000555555')
    data = json.loads(resp.read())
    for c in data['courses']:
        print(f"{c['codigo']} {c['nombre']} - secciones: {len(c['secciones'])}")
except Exception as e:
    print(e)
