# nlp_utils.py

import spacy
from .crud import get_student_info, enroll_student_in_subject, cancel_subject, list_enrollments
from .intents import INTENT_VOCABULARY
import re

nlp = spacy.load("es_core_news_sm")
last_message = None

def detect_intent(doc):
    for intent, keywords in INTENT_VOCABULARY.items():
        if any(token.lemma_ in keywords for token in doc):
            print(f"Intención detectada: {intent}")  # Depuración
            return intent
    print("Ninguna intención detectada")
    return None

def extract_subject_code(doc):
    pattern = r"[A-Z]{3}\d+"
    text = doc.text
    print(f"Texto para buscar código de materia: '{text}'")
    match = re.search(pattern, text)
    if match:
        print(f"Código de materia detectado: {match.group(0)}")  # Depuración
    else:
        print("No se encontró código de materia")  # Depuración
    return match.group(0) if match else None

def process_nlp_and_act(user_input: str, student_id: int = None):
    global last_message

    # Detectar mensaje repetido
    if user_input == last_message:
        return {
            "message": "Parece que estás enviando el mismo mensaje varias veces. ¿Hay algo más en lo que puedo ayudarte?",
            "repeat_warning": True
        }
    
    last_message = user_input  # Actualizar último mensaje
    
    # Procesar el saludo del usuario y pedir el código de estudiante si no lo tenemos
    doc = nlp(user_input)
    intent = detect_intent(doc)

    if intent == "saludo" and student_id is None:
        return {
            "message": "¡Bienvenid@! Antes de continuar, por favor ingresa tu código de estudiante."
        }

    # 2. Solicitar el código de estudiante si aún no ha sido ingresado
    if student_id is None:
        if user_input.isdigit():  # Si el usuario envía el `student_id` como un número
            student_id = int(user_input)
            student_info = get_student_info(student_id)
            if student_info:
                message = (
                    f"¡Interesante!, {student_info['name']}.\n"
                    f" Estás en el semestre {student_info['current_semester']}.\n"
                    
                    + "Materias inscritas:\n"
                    + "\n".join(f"- {subject['name']} ({subject['status']})" for subject in student_info["subjects"])
                    + f"\nCréditos usados: {student_info['credits_used']}\n"
                    + "¿Qué deseas hacer? Puedes 'inscribir', 'cancelar' o 'listar' materias."
                )
                return {"message": message, "student_id": student_id, "student_info": student_info}
            else:
                return {"message": "No se encontró un estudiante con ese código. Por favor intenta nuevamente."}
        return {"message": "Por favor, ingresa tu código de estudiante para continuar."}

    # 3. Manejo de intención de "salir"
    if intent == "salir":
        return {
            "message": "Gracias por utilizar el chatbot. ¡Hasta luego!",
            "exit": True
        }

    # Solicitar ID del estudiante si no está presente
    if intent == "saludo" and student_id is None:
        return {"message": "¡Hola! Antes de continuar, por favor ingresa tu código de estudiante."}

    # Obtener y validar información del estudiante
    if student_id is None and user_input.isdigit():
        student_id = int(user_input)
        student_info = get_student_info(student_id)

        if student_info:
            message = (
                f"Hola, {student_info['name']}. Estás en el semestre {student_info['current_semester']}.\n"
                + "Materias inscritas:\n"
                + "\n".join(f"- {subject['name']} ({subject['status']})" for subject in student_info["subjects"])
                + f"\nCréditos usados: {student_info['credits_used']}\n"
                + "¿Qué deseas hacer? Puedes 'inscribir', 'cancelar' o 'listar' materias."
            )
            return {"message": message, "student_id": student_id, "student_info": student_info}

    # Procesar acciones de inscribir, cancelar o listar
    if student_id:
        student_info = get_student_info(student_id)

        if intent == "inscribir":
            subject_code = extract_subject_code(doc)
            if subject_code:
                return enroll_student_in_subject({"id": student_id, "current_semester": student_info["current_semester"]}, subject_code)
            return {"message": "Por favor, proporciona el código de la materia que deseas inscribir."}

        elif intent == "cancelar":
            subject_code = extract_subject_code(doc)
            if subject_code:
                return cancel_subject(student_id, subject_code, student_info["current_semester"])
            return {"message": "Por favor, proporciona el código de la materia que deseas cancelar."}

        elif intent == "listar":
            return list_enrollments(student_id, student_info["current_semester"])

    # Mensaje de error si no se detecta intención válida
    return {"message": "Lo siento, no entendí tu solicitud. Por favor intenta nuevamente."}
