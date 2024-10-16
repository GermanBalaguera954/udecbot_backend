#nlp_utils.py

import spacy
from fastapi import HTTPException
from .crud import enroll_subject, cancel_subject
from .models import CancelRequest  # Importar desde models.py

# Cargar el modelo de spaCy en español
nlp = spacy.load("es_core_news_md")

def process_nlp_and_act(user_input: str, student_id: int, current_semester: int):
    doc = nlp(user_input)
    
    # Detectar intención de inscribir o cancelar
    if "inscribir" in user_input.lower():
        # Extraer el código de la materia a partir del input (si está disponible)
        subject_code = None
        for ent in doc.ents:
            if ent.label_ == "MISC":  # Suponiendo que las materias se etiquetan como MISC
                subject_code = ent.text
        
        if not subject_code:
            raise HTTPException(status_code=400, detail="No se encontró un código de materia válido para inscribir.")
        
        # Llamar a la función de inscripción
        result = enroll_subject(student_id, subject_code, current_semester, current_semester)
        return result
    
    elif "cancelar" in user_input.lower():
        subject_code = None
        for ent in doc.ents:
            if ent.label_ == "MISC":
                subject_code = ent.text
        
        if not subject_code:
            raise HTTPException(status_code=400, detail="No se encontró un código de materia válido para cancelar.")
        
        # Llamar a la función de cancelación
        request = CancelRequest(student_id=student_id, subject_code=subject_code, current_semester=current_semester)
        result = cancel_subject(request.student_id, request.subject_code, request.current_semester)
        return result

    else:
        return {"message": "No se pudo identificar la acción solicitada. Intenta inscribir o cancelar una materia."}