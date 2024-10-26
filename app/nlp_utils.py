import spacy
from .crud import get_student_info, enroll_dn_cai, enroll_subject
import re

# Cargar el modelo de SpaCy para el procesamiento de lenguaje natural
nlp = spacy.load("es_core_news_sm")

# Detectar intenciones con base en el input del usuario
def detect_intent(doc):
    for token in doc:
        if token.lemma_ in ["hola", "saludar", "buenas", "qué tal", "qué más", "cómo estás", "dia", "tarde", "noche"]:
            return "saludo"
        elif token.lemma_ in ["inscribir", "matricular", "añadir"]:
            return "inscribir"
    return None  # Devuelve None si no se encuentra una intención

# Procesar el input del usuario y realizar la acción correspondiente
def process_nlp_and_act(user_input: str, student_id: int = None, saludo_inicial=False, inscribir_estado=False):
    # Crear el documento de SpaCy con el input del usuario
    doc = nlp(user_input.lower())
    intent = detect_intent(doc)

    # 1. Saludo inicial del chatbot
    if not saludo_inicial:
        return {
            "message": "¡Hola! Soy udecbot, tu asistente virtual. "
        }

    # 2. El usuario responde con un saludo
    if intent == "saludo" and student_id is None:
        # Formato de mensaje como HTML
        message = """
        <p>¿En qué puedo ayudarte hoy?</p>
        <p>Puedo asistirte en las siguientes opciones:</p>
        <ul>
            <li>Inscribir o cancelar materias</li>
            <li>Listar tus materias actuales</li>
            <li>Consultar los créditos que has usado</li>
        </ul>
        <p>Por favor, ingresa tu código de estudiante para continuar.</p>
        """
        return {"message": message}

    if student_id is None and user_input.isdigit():
        student_id = int(user_input)
        student_info = get_student_info(student_id)

        if student_info:
            # Mensaje completo con la información organizada
            message = f"""
                <p>Esta es la información que tengo actualmente para <strong>{student_info['name']}</strong>:</p>
                <p>Semestre actual: {student_info['current_semester']}</p>
                <p>Materias actuales:</p>
                <ol>
            """
            for subject in student_info["subjects"]:
                message += f"<li>{subject['name']} ({subject['status']})</li>"

            message += f"""
                </ol>
                <p>Créditos usados actualmente: {student_info['credits_used']}</p>
                <p>¿Qué deseas hacer....................?</p>
                
            """
            return {"message": message, "inscribir_estado": False}

        else:
            return {"message": "No se encontró información para el código de estudiante proporcionado. Por favor verifica el ID e inténtalo nuevamente."}

    # Si el usuario solicita inscribir, ejecuta ambas funciones
    if intent == "inscribir" and student_id is not None:
        try:
            # 1. Ejecutar inscripción de DN CAI automáticamente
            enroll_dn_cai(student_id)
            dn_cai_message = "Las materias DN CAI han sido inscritas automáticamente."

            # 2. Solicitar al usuario el código de la materia específica
            return {
                "message": f"{dn_cai_message} Por favor, ingresa el código de la materia específica que deseas inscribir.",
                "inscribir_estado": True  # Para esperar el código de materia específica
            }
        except Exception as e:
            return {"message": f"Error al intentar inscribir materias DN CAI: {str(e)}"}

    # Inscribir materia específica cuando el usuario ingrese el código
    if inscribir_estado and student_id is not None:
        enroll_response = enroll_subject(student_id, user_input)
        return enroll_response  # Responde con el mensaje de inscripción

    # Mensaje para acciones no reconocidas
    return {"message": "No se pudo identificar la acción solicitada. Intenta con 'inscribir', 'cancelar', 'listar' o 'consultar créditos'."}