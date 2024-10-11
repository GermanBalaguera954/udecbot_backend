from fastapi import FastAPI, HTTPException
from .crud import enroll_subject, list_enrollments, check_first_time
from .database import get_db_connection

app = FastAPI()

@app.get("/prueba_conexion")
def prueba_conexion():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")  # Consulta simple para probar la conexión
        cur.close()
        conn.close()
        return {"message": "Conexión exitosa a la base de datos"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la conexión: {str(e)}")

@app.get("/chat/start/{student_id}")
def start_chat(student_id: int):
    # Validar si el estudiante ya interactuó antes
    is_first_time = check_first_time(student_id)
    
    # Mostrar las opciones al estudiante
    if is_first_time:
        return {
            "message": "Bienvenido por primera vez. ¿Qué deseas hacer?",
            "options": ["1. Inscribir materia", "2. Cancelar materia", "3. Listar materias", "4. Salir"]
        }
    else:
        return {
            "message": "Bienvenido de nuevo. ¿Qué deseas hacer?",
            "options": ["1. Inscribir materia", "2. Cancelar materia", "3. Listar materias", "4. Salir"]
        }

@app.post("/chat/inscribir")
def inscribir_materia(student_id: int, subject_code: str):
    try:
        enroll_subject(student_id, subject_code)
        return {"message": "Materia inscrita exitosamente."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/chat/cancelar")
def cancelar_materia(student_id: int, subject_code: str):
    # Lógica para cancelar una materia
    return {"message": f"Materia {subject_code} cancelada para el estudiante {student_id}."}

@app.get("/chat/listar/{student_id}")
def listar_materias(student_id: int):
    subjects = list_enrollments(student_id)
    return {"message": "Materias inscritas:", "subjects": subjects}
