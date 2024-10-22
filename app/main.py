#main.py

from fastapi import FastAPI, HTTPException
from .crud import enroll_subject, list_enrollments, check_first_time, cancel_subject, list_used_credits
from .database import get_db_connection
from .nlp_utils import process_nlp_and_act
from .models import EnrollRequest, CancelRequest
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/prueba_conexion")
def prueba_conexion():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        return {"message": "Conexión exitosa a la base de datos"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la conexión: {str(e)}")

@app.get("/chat/start/{student_id}")
def start_chat(student_id: int):
    is_first_time = check_first_time(student_id)
    
    # Personalizamos el mensaje dependiendo de si es la primera vez o no
    if is_first_time:
        return {
            "message": "Bienvenido por primera vez al sistema de inscripción. ¿Qué deseas hacer?",
            "options": ["1. Inscribir materia", "2. Cancelar materia", "3. Listar materias", "4. Salir"]
        }
    else:
        return {
            "message": "Bienvenido de nuevo. ¿Qué deseas hacer hoy?",
            "options": ["1. Inscribir materia", "2. Cancelar materia", "3. Listar materias", "4. Salir"]
        }

@app.post("/chat/inscribir")
def inscribir_materia(request: EnrollRequest):
    try:
        result = enroll_subject(request.student_id, request.subject_code)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/chat/cancelar")
def cancelar_materia(request: CancelRequest):
    try:
        result = cancel_subject(request.student_id, request.subject_code)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/chat/listar/{student_id}")
def listar_materias(student_id: int):
    subjects = list_enrollments(student_id)
    return {"message": "Materias inscritas:", "subjects": subjects}

@app.post("/chat/nlp")
def handle_nlp(user_input: str, student_id: int):
    return process_nlp_and_act(user_input, student_id)

@app.get("/credits/{student_id}")
def obtener_creditos_usados(student_id: int):
    try:
        resultado = list_used_credits(student_id)
        return {"message": f"El estudiante ha usado {resultado['total_credits_used']} créditos en el semestre {resultado['current_semester']}."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
