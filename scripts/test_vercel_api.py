import urllib.request
import urllib.error

endpoints = [
    'https://prediccion-horarios-ae.vercel.app/api/student-info?codigo=000555555',
    'https://prediccion-horarios-ae.vercel.app/api/eligible-courses?codigo=000555555'
]

for url in endpoints:
    print(f"\nProbando: {url}")
    try:
        with urllib.request.urlopen(url) as resp:
            print("HTTP 200 OK:", resp.read().decode('utf-8')[:300])
    except urllib.error.HTTPError as e:
        print(f"HTTP ERROR {e.code}:", e.read().decode('utf-8'))
    except Exception as e:
        print("ERROR:", e)
