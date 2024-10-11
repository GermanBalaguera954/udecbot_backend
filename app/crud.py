from .database import get_db_connection

def check_first_time(student_id: int):
    # Revisar si el estudiante tiene materias inscritas
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM enrollments WHERE student_id = %s", (student_id,))
    enrollments = cur.fetchall()
    cur.close()
    conn.close()
    
    # Si no hay inscripciones, es la primera vez que interactúa
    if len(enrollments) == 0:
        return True
    return False

def enroll_subject(student_id: int, subject_code: str):
    # Validar si el estudiante puede inscribir la materia
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Revisar si ya alcanzó el límite de créditos
    cur.execute("""
        SELECT SUM(subjects.credits) as total_credits 
        FROM enrollments 
        JOIN subjects ON enrollments.subject_code = subjects.code 
        WHERE enrollments.student_id = %s
    """, (student_id,))
    total_credits = cur.fetchone()['total_credits'] or 0
    
    if total_credits >= 18:
        raise Exception("No puedes inscribir más materias, ya has alcanzado el límite de 18 créditos.")
    
    # Inscribir la materia
    cur.execute("""
        INSERT INTO enrollments (student_id, subject_code, enrollment_date) 
        VALUES (%s, %s, NOW())
    """, (student_id, subject_code))
    conn.commit()
    cur.close()
    conn.close()

def list_enrollments(student_id: int):
    # Listar las materias inscritas
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT subjects.code, subjects.name, subjects.credits 
        FROM enrollments 
        JOIN subjects ON enrollments.subject_code = subjects.code 
        WHERE enrollments.student_id = %s
    """, (student_id,))
    subjects = cur.fetchall()
    cur.close()
    conn.close()
    return subjects
