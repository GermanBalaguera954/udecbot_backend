# nlp_utils.py

import spacy
from sentence_transformers import SentenceTransformer, util
from .crud import get_student_info, enroll_student_in_subject, cancel_subject, list_enrollments
from .intents import INTENT_VOCABULARY
import re

# Cargar el modelo de embeddings
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

nlp = spacy.load("es_core_news_sm")
last_message = None

# Preparar ejemplos de intenciones y calcular sus embeddings
def load_intent_embeddings():
    intent_embeddings = {}
    for intent, examples in INTENT_VOCABULARY.items():
        intent_embeddings[intent] = [embedding_model.encode(example) for example in examples]
    return intent_embeddings

intent_embeddings = load_intent_embeddings()

def detect_intent(doc):
    # Convertir el mensaje en un embedding
    message_embedding = embedding_model.encode(doc.text)
    
    # Calcular la similitud entre el embedding del mensaje y las intenciones
    best_intent = None
    highest_similarity = 0.0
    
    for intent, embeddings in intent_embeddings.items():
        for intent_embedding in embeddings:
            similarity = util.cos_sim(message_embedding, intent_embedding).item()
            if similarity > highest_similarity:
                highest_similarity = similarity
                best_intent = intent
    
    # Establecer un umbral de similitud para detectar la intención
    if highest_similarity >= 0.5:
        print(f"Intención detectada: {best_intent} (similitud: {highest_similarity})")
        return best_intent
    else:
        print("Ninguna intención detectada con alta similitud")
        return None

def extract_subject_code(doc):
    pattern = r"[A-Z]{3}\d+"
    text = doc.text
    print(f"Texto para buscar código de materia: '{text}'")
    match = re.search(pattern, text)
    if match:
        print(f"Código de materia detectado: {match.group(0)}")
    else:
        print("No se encontró código de materia")
    return match.group(0) if match else None

def process_nlp_and_act(user_input: str, student_id: int = None):
    global last_message

    if user_input == last_message:
        return {
            "message": "Parece que estás enviando el mismo mensaje varias veces. ¿Hay algo más en lo que puedo ayudarte?",
            "repeat_warning": True
        }
    
    last_message = user_input
    
    # Procesar el saludo del usuario y pedir el código de estudiante si no lo tenemos
    doc = nlp(user_input)
    intent = detect_intent(doc)

    if intent == "saludo" and student_id is None:
        return {
            "message": "\t\t¡Bienvenid@!\n\n" 
            "Antes de continuar.\n\n" 
            "Por favor ingresa tu código de estudiante."
        }

    # Solicitar el código de estudiante si aún no ha sido ingresado
    if student_id is None:
        if user_input.isdigit():
            student_id = int(user_input)
            student_info = get_student_info(student_id)
            if student_info:
                message = (
                    f"\t\t¡Interesante!.......... {student_info['name']}.\n\n"
                    f" Estás en el semestre {student_info['current_semester']}.\n\n"
                    + "Materias inscritas:\n"
                    + "\n".join(f"- {subject['name']} ({subject['status']})" for subject in student_info["subjects"])
                    + f"\n\nCréditos usados: {student_info['credits_used']}\n\n"
                    + "¿Qué deseas hacer? \n\n"
                    + "Puedes 'inscribir', 'cancelar' o 'listar' materias."
                )
                return {"message": message, "student_id": student_id, "student_info": student_info}
            else:
                return {"message": "No se encontró un estudiante con ese código. Por favor intenta nuevamente."}

    # Manejo de intención de "salir"
    if intent == "salir":
        return {
            "message": "Gracias por utilizar el chatbot. ¡Hasta luego!",
            "exit": True
        }

    # Procesar acciones de inscribir, cancelar o listar
    if student_id:
        student_info = get_student_info(student_id)

        if intent == "inscribir":
            subject_code = extract_subject_code(doc)
            if subject_code:
                return enroll_student_in_subject({"id": student_id, "current_semester": student_info["current_semester"]}, subject_code)
            return {"message": "Por favor, digita el código de la materia que deseas inscribir.\n"}

        elif intent == "cancelar":
            subject_code = extract_subject_code(doc)
            if subject_code:
                return cancel_subject(student_id, subject_code, student_info["current_semester"])
            return {"message": "Por favor, proporciona el código de la materia que deseas cancelar."}

        elif intent == "listar":
            return list_enrollments(student_id, student_info["current_semester"])

    # Mensaje de error si no se detecta intención válida
    return {"message": "Lo siento, no entendí tu solicitud. Por favor intenta nuevamente."}
