import spacy
from sentence_transformers import SentenceTransformer, util
from nltk.stem import SnowballStemmer
from .crud import get_student_info, enroll_student_in_subject, cancel_subject, list_enrollments
from .intents import INTENT_VOCABULARY
import re

# Cargar modelos y herramientas
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
nlp = spacy.load("es_core_news_sm")
stemmer = SnowballStemmer("spanish")

last_message = None
last_intent = None  # Almacena la última intención detectada para contexto

# Función para cargar embeddings de intenciones
def load_intent_embeddings():
    intent_embeddings = {}
    for intent, examples in INTENT_VOCABULARY.items():
        intent_embeddings[intent] = [embedding_model.encode(example) for example in examples]
    return intent_embeddings

intent_embeddings = load_intent_embeddings()

def detect_intent(doc):
    # Embedding de la frase completa
    message_embedding = embedding_model.encode(doc.text)
    best_intent = None
    highest_similarity = 0.0
    similarity_threshold = 0.5

    # Comparar embeddings de intenciones
    for intent, embeddings in intent_embeddings.items():
        for intent_embedding in embeddings:
            similarity = util.cos_sim(message_embedding, intent_embedding).item()
            if similarity > highest_similarity:
                highest_similarity = similarity
                best_intent = intent

    return best_intent if highest_similarity >= similarity_threshold else None

# Detecta si el mensaje es un código de materia
def is_subject_code(text):
    pattern = r"^[A-Z]{3}\d{6,}$"
    return re.match(pattern, text) is not None

# Procesa el mensaje y actúa en base a la intención
def process_nlp_and_act(user_input: str, student_id: int):
    student_info = get_student_info(student_id)
    if student_info is None:
        return {"message": "No se encontró el estudiante en el sistema.", "error": True}

    global last_message, last_intent  # Acceder a las variables globales

    # Evitar repetir la misma acción
    if user_input == last_message:
        return {"message": "Parece que estás enviando el mismo mensaje varias veces. ¿Quieres hacer algo diferente?", "repeat_warning": True}
    
    last_message = user_input  # Actualizar el último mensaje

    doc = nlp(user_input)

    # Detectar intención
    intent = detect_intent(doc)

    # Detectar códigos de materia
    if is_subject_code(user_input):
        return handle_subject_code_intent(user_input, student_id)

    # Procesar intención específica
    if intent == "saludo":
        last_intent = "saludo"  # Actualizar la última intención
        return handle_greeting(student_id)
    elif intent == "inscribir":
        last_intent = "inscribir"  # Actualizar la última intención
        return handle_enroll_request()
    elif intent == "cancelar":
        last_intent = "cancelar"  # Actualizar la última intención
        return handle_cancel_request()
    elif intent == "listar":
        last_intent = "listar"  # Actualizar la última intención
        return handle_list_enrollments(student_id)
    elif intent == "salir":
        last_intent = "salir"  # Actualizar la última intención
        return handle_exit()

    # Respuesta por defecto si no hay intención detectada
    return {"message": "Lo siento, no entendí tu solicitud. Por favor intenta nuevamente."}

# Maneja cada intención específica
def handle_subject_code_intent(user_input, student_id):
    if last_intent == "inscribir":
        return enroll_student_in_subject(
            {"id": student_id, "current_semester": get_student_info(student_id)["current_semester"]},
            user_input
        )
    elif last_intent == "cancelar":
        return cancel_subject(student_id, user_input)  # Eliminar `current_semester`
    else:
        return {"message": "Por favor, indica si deseas inscribir o cancelar la materia."}

def handle_greeting(student_id):
    student_info = get_student_info(student_id)
    message = (
        f"Hola, {student_info['name']}.\n"
        f"Estás en el semestre {student_info['current_semester']}.\n\n"
        "¿Qué deseas hacer? Puedes 'inscribir', 'cancelar' o 'listar' materias."
    )
    return {"message": message}

def handle_enroll_request():
    return {"message": "Por favor, digita el código de la materia que deseas inscribir.",
            "link": "https://acortar.link/zA3Dl5"}

def handle_cancel_request():
    return {"message": "Por favor, proporciona el código de la materia que deseas cancelar.",
            "link": "https://acortar.link/zA3Dl5"}

def handle_list_enrollments(student_id):
    return list_enrollments(student_id)

def handle_exit():
    return {"message": "Gracias por utilizar el chatbot. ¡Hasta luego!", "exit": True}
