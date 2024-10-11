#main.py
from fastapi import FastAPI, HTTPException
from .crud import enroll_subject, list_enrollments, check_first_time
from .database import get_db_connection
from pydantic import BaseModel


# Definir el esquema Pydantic para los datos entrantes
class EnrollRequest(BaseModel):
    student_id: int
    subject_code: str
    current_semester: int  # Agregar el semestre actual del estudiante

class CancelRequest(BaseModel):
    student_id: int
    subject_code: str

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
def inscribir_materia(request: EnrollRequest):
    try:
        # Eliminar el parámetro "semester" si no es necesario
        result = enroll_subject(request.student_id, request.subject_code, request.current_semester, request.current_semester)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Ruta para cancelar materias con POST
@app.post("/chat/cancelar")
def cancelar_materia(request: CancelRequest):
    conn = get_db_connection()
    cur = conn.cursor()

    # Obtener información de la materia para validar el semestre
    cur.execute("""
        SELECT semester FROM subjects WHERE code = %s
    """, (request.subject_code,))
    
    subject_info = cur.fetchone()

    if not subject_info:
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail=f"La materia con el código {request.subject_code} no existe.")

    # Validar si la materia pertenece al semestre actual
    if subject_info['semester'] != request.current_semester:
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail=f"No puedes cancelar la materia {request.subject_code} porque no pertenece a tu semestre actual.")

    # Verificar si la materia está inscrita
    cur.execute("""
        SELECT * FROM enrollments 
        WHERE student_id = %s AND subject_code = %s
    """, (request.student_id, request.subject_code))
    
    existing_enrollment = cur.fetchone()

    if not existing_enrollment:
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail=f"La materia {request.subject_code} no está inscrita para el estudiante {request.student_id}.")

    # Cancelar la materia
    cur.execute("""
        DELETE FROM enrollments 
        WHERE student_id = %s AND subject_code = %s
    """, (request.student_id, request.subject_code))
    
    conn.commit()
    cur.close()
    conn.close()

    return {"message": f"Materia {request.subject_code} cancelada exitosamente para el estudiante {request.student_id}."}


@app.get("/chat/listar/{student_id}")
def listar_materias(student_id: int):
    subjects = list_enrollments(student_id)
    return {"message": "Materias inscritas:", "subjects": subjects}
