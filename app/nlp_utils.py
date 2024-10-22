# nlp_utils.py

import spacy
from fastapi import HTTPException
from .crud import enroll_subject, cancel_subject, list_enrollments, list_used_credits

# Cargar el modelo preentrenado
nlp = spacy.load("es_core_news_sm")

# Función para extraer el código de materia
def extract_subject_code(doc):
    for ent in doc.ents:
        if ent.label_ == "MATERIA":
            return ent.text
    return None

# Función para procesar el lenguaje natural y realizar acciones
def process_nlp_and_act(user_input: str, student_id: int):
    doc = nlp(user_input.lower())

    materias = [ent.text for ent in doc.ents if ent.label_ == "MATERIA"]

    # Acciones que se pueden identificar en el input del usuario
    if any(intent in user_input for intent in ["inscribir", "inscribirme", "quiero inscribir"]):
        if materias:
            subject_code = materias[0]  # Usa la primera materia detectada
            return enroll_subject(student_id, subject_code)
        else:
            raise HTTPException(status_code=400, detail="No se encontró un código de materia válido para inscribir.")

    elif any(intent in user_input for intent in ["cancelar", "quiero cancelar", "me gustaría cancelar"]):
        if materias:
            subject_code = materias[0]  # Usa la primera materia detectada
            return cancel_subject(student_id, subject_code)
        else:
            raise HTTPException(status_code=400, detail="No se encontró un código de materia válido para cancelar.")

    elif any(intent in user_input for intent in ["listar materias", "ver materias", "mostrar materias"]):
        return list_enrollments(student_id)

    elif any(intent in user_input for intent in ["creditos usados", "consultar creditos", "cuántos créditos he usado"]):
        resultado = list_used_credits(student_id)
        return {
            "message": f"El estudiante ha usado {resultado['total_credits_used']} créditos en el semestre {resultado['current_semester']}."
        }

    elif any(intent in user_input for intent in ["ayuda", "información", "necesito ayuda"]):
        return {
            "message": "Puedes inscribir o cancelar materias, listar tus materias actuales o consultar tus créditos usados."
        }

    else:
        return {"message": "No se pudo identificar la acción solicitada. Intenta inscribir, cancelar, listar materias o consultar créditos."}
