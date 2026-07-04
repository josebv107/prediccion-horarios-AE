# Sistema de Predicción de Matrícula y Horarios (UPAO)

Bienvenido al repositorio del **Sistema de Predicción de Matrícula y Horarios**. Este proyecto es una aplicación web diseñada para asistir a los estudiantes universitarios en la selección de sus cursos, integrando un modelo de Machine Learning que predice la probabilidad de éxito (aprobación) del alumno basado en su rendimiento histórico, créditos matriculados y el índice de exigencia de los docentes seleccionados.

🔗 **Enlace al proyecto en vivo:** [https://prediccion-horarios-ae.vercel.app/](https://prediccion-horarios-ae.vercel.app/)

---

## 7.1.1 Pestaña de Documentación del Proyecto

En esta sección se detallan los aspectos teóricos y técnicos fundamentales del sistema:

* **Objetivo:** Facilitar la creación de horarios académicos óptimos y advertir a los estudiantes sobre posibles riesgos de sobrecarga académica mediante inteligencia artificial.
* **Arquitectura:** 
  * **Frontend:** Desarrollado con HTML5, CSS3 y JavaScript puro (Vanilla JS). Implementa una interfaz inspirada en Canvas Instructure.
  * **Backend:** API Serverless alojada en Vercel utilizando Python.
  * **Base de Datos:** SQLite (`db/upao_new.db`) para almacenar mallas curriculares, históricos de notas, docentes y horarios.
  * **Modelo de Machine Learning:** Utiliza `scikit-learn` (`RandomForestClassifier` y `GradientBoostingClassifier`) para procesar características como el promedio histórico, balance de horas, horas libres y dificultad ponderada.

## 7.1.2 Pestaña de Código del Sistema

El código fuente está estructurado de la siguiente manera para un fácil mantenimiento y despliegue:

* `/api/index.py`: Contiene el manejador principal (Backend) que procesa las peticiones de la API (login, consulta de cursos, motor de recomendación) y lo expone a través del entorno Serverless de Vercel.
* `/index.html`: La interfaz principal del simulador de matrícula interactivo.
* `/css/` y `/js/`: Hojas de estilo y lógica del lado del cliente que gestionan el carrito de compras (cursos), bloqueos por choques de horarios, y comunicación con la API.
* `/db/`: Contiene la base de datos preconfigurada con todo el catálogo de horarios de la universidad.
* `/predictor.py`: Módulo independiente encargado del procesamiento de datos, escalado y predicción a través del modelo de ensamble de Machine Learning.
* `/images/`: Todos los recursos estáticos visuales de la aplicación.

## 7.1.3 Pestaña de Ejecución y Pruebas del Sistema

Para ejecutar este proyecto en tu entorno local (localhost) o visualizar las pruebas:

**Requisitos previos:**
* Python 3.9 o superior.
* Librerías listadas en `requirements.txt` (Instalar usando `pip install -r requirements.txt`).

**Ejecución en Local:**
1. Clona este repositorio en tu máquina local.
2. Abre una terminal en la raíz del proyecto.
3. Ejecuta el archivo servidor de pruebas locales con el comando:
   ```bash
   python server.py
   ```
4. Abre tu navegador e ingresa a `http://localhost:8000`.

**Usuarios de Prueba:**
Para acceder al sistema y probar la plataforma, puedes usar cualquiera de los siguientes códigos de estudiante como usuario (la contraseña es la misma que el usuario o dejar en blanco si el entorno de desarrollo lo permite):
* `000555555` (Estudiante de 2do ciclo)
* `000999999` (Estudiante de 4to ciclo, con deudas previas)

Una vez logueado, puedes seleccionar combinaciones de horarios y hacer clic en **"Predecir Aprobación"** para evaluar el desempeño del modelo.
