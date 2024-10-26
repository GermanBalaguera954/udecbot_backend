from fastapi import FastAPI, HTTPException
from .crud import enroll_subject, list_enrollments, cancel_subject, list_used_credits
from .nlp_utils import process_nlp_and_act
from .models import EnrollRequest, CancelRequest
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError, BaseModel

app = FastAPI()

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelo para la solicitud de interacción
class InteractRequest(BaseModel):
    user_input: str
    student_id: int = None
    saludo_inicial: bool = False  # Indica si ya se envió el saludo inicial
    inscribir_estado: bool = False  # Indica si se está en proceso de inscripción de materia específica

@app.post("/interact/")
def interact(request: InteractRequest):
    try:
        # Llama a process_nlp_and_act con los parámetros adicionales
        response = process_nlp_and_act(
            request.user_input,
            request.student_id,
            request.saludo_inicial,
            request.inscribir_estado
        )
        
        # Devuelve la respuesta del procesamiento NLP al frontend
        if isinstance(response, dict) and "message" in response:
            return response
        else:
            return {"message": "Respuesta inesperada del procesamiento NLP"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error procesando la solicitud: {str(e)}")





# Inscribir materia
@app.post("/chat/inscribir")
def inscribir_materia(request: EnrollRequest):
    try:
        if not request.student_id or not request.subject_code:
            raise HTTPException(status_code=422, detail="Faltan datos: el ID del estudiante y el código de la materia son obligatorios.")
        result = enroll_subject(request.student_id, request.subject_code)
        return result
    except ValidationError as ve:
        raise HTTPException(status_code=422, detail=f"Datos inválidos: {ve}")
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

# Cancelar materia
@app.post("/chat/cancelar")
def cancelar_materia(request: CancelRequest):
    try:
        result = cancel_subject(request.student_id, request.subject_code)
        return result
    except ValidationError as ve:
        raise HTTPException(status_code=422, detail=f"Datos inválidos: {ve}")
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

# Listar materias inscritas
@app.get("/chat/listar/{student_id}")
def listar_materias(student_id: int):
    try:
        subjects = list_enrollments(student_id)
        if not subjects:
            return {"message": "No tienes materias inscritas."}
        return {"message": "Materias inscritas:", "subjects": subjects}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

# Consultar créditos usados
@app.get("/credits/{student_id}")
def obtener_creditos_usados(student_id: int):
    try:
        resultado = list_used_credits(student_id)
        return {
            "message": f"El estudiante ha usado {resultado['total_credits_used']} créditos en el semestre {resultado['current_semester']}."
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
