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

# Función para inscribir automáticamente las materias DN CAI
def enroll_dn_cai(student_id: int, semester: int):
    conn = get_db_connection()
    cur = conn.cursor()

    # Buscar materias DN CAI para el semestre actual del estudiante
    cur.execute("""
        SELECT code FROM subjects 
        WHERE semester = %s AND credits = 0 AND code LIKE 'DN-%%'
    """, (semester,))
    
    dn_cai_subjects = cur.fetchall()

    # Inscribir cada materia DN CAI si no está inscrita
    for subject in dn_cai_subjects:
        cur.execute("""
            SELECT * FROM enrollments 
            WHERE student_id = %s AND subject_code = %s
        """, (student_id, subject['code']))
        
        existing_enrollment = cur.fetchone()

        if not existing_enrollment:
            cur.execute("""
                INSERT INTO enrollments (student_id, subject_code, enrollment_date) 
                VALUES (%s, %s, NOW())
            """, (student_id, subject['code']))
            conn.commit()

    cur.close()
    conn.close()

def enroll_subject(student_id: int, subject_code: str, semester: int, current_semester: int):
    conn = get_db_connection()
    cur = conn.cursor()

    # Obtener el semestre actual del estudiante desde la base de datos
    cur.execute("""
        SELECT current_semester FROM students WHERE id = %s
    """, (student_id,))
    
    student_info = cur.fetchone()

    if not student_info:
        cur.close()
        conn.close()
        raise Exception(f"No se encontró información del estudiante con ID {student_id}.")
    
    # Verificar si el semestre ingresado coincide con el semestre real del estudiante
    if current_semester != student_info['current_semester']:
        cur.close()
        conn.close()
        raise Exception(f"El semestre ingresado ({current_semester}) no coincide con el semestre real del estudiante ({student_info['current_semester']}).")

    # Verificar si el código de la materia corresponde al semestre ingresado
    cur.execute("""
        SELECT semester, requirements FROM subjects WHERE code = %s
    """, (subject_code,))
    
    subject_info = cur.fetchone()

    if not subject_info:
        cur.close()
        conn.close()
        raise Exception(f"La materia con el código {subject_code} no existe.")
    
    # Validar si el estudiante ha cumplido los requisitos de la materia
    if subject_info['requirements'] and subject_info['requirements'].strip():
        requirements = subject_info['requirements'].split(', ')
        for req in requirements:
            # Validar si el estudiante ha inscrito y aprobado el prerrequisito
            cur.execute("""
                SELECT * FROM enrollments 
                WHERE student_id = %s AND subject_code = %s AND status = 'passed'
            """, (student_id, req.replace('R - ', '')))
            if not cur.fetchone():
                cur.close()
                conn.close()
                raise Exception(f"No puedes inscribir {subject_code} porque no has aprobado el prerrequisito {req.replace('R - ', '')}.")

    # Verificar si el estudiante ha inscrito todas las materias del semestre actual o si está repitiendo una materia
    if subject_info['semester'] > current_semester:
        # Verificar cuántas materias del semestre actual están inscritas
        cur.execute("""
            SELECT COUNT(*) as total_inscritas
            FROM enrollments 
            JOIN subjects ON enrollments.subject_code = subjects.code
            WHERE enrollments.student_id = %s AND subjects.semester = %s
        """, (student_id, current_semester))
        
        total_inscritas = cur.fetchone()['total_inscritas']

        # Contar cuántas materias hay en el semestre actual
        cur.execute("""
            SELECT COUNT(*) as total_materias
            FROM subjects 
            WHERE semester = %s AND credits > 0
        """, (current_semester,))
        
        total_materias = cur.fetchone()['total_materias']

        # Verificar si el estudiante está repitiendo una materia
        cur.execute("""
            SELECT COUNT(*) as total_reprobadas
            FROM enrollments 
            WHERE student_id = %s AND status = 'failed'
        """, (student_id,))
        
        total_reprobadas = cur.fetchone()['total_reprobadas']

        # Si no ha inscrito todas las materias y no está repitiendo ninguna, bloquear la inscripción
        if total_inscritas < total_materias and total_reprobadas == 0:
            cur.close()
            conn.close()
            raise Exception(f"No puedes adelantar materias sin inscribir todas las materias del semestre actual. Te faltan {total_materias - total_inscritas} materias por inscribir.")
        
        # Si está repitiendo, permitir la inscripción siempre que el número de materias inscritas + reprobadas sea suficiente
        if total_inscritas + total_reprobadas < total_materias:
            cur.close()
            conn.close()
            raise Exception(f"No puedes adelantar materias. Debes inscribir todas las materias obligatorias del semestre actual o repetir las que perdiste.")

    # Validar si la materia corresponde al semestre actual o si se puede adelantar
    if subject_info['semester'] > current_semester + 2:
        cur.close()
        conn.close()
        raise Exception(f"No puedes adelantar más de dos semestres. La materia {subject_code} pertenece al semestre {subject_info['semester']}.")

    # Validar que la materia no sea de un semestre anterior, a menos que haya sido reprobada
    if subject_info['semester'] < current_semester:
        cur.execute("""
            SELECT * FROM enrollments 
            WHERE student_id = %s AND subject_code = %s AND status = 'failed'
        """, (student_id, subject_code))
        
        failed_subject = cur.fetchone()

        if not failed_subject:
            cur.close()
            conn.close()
            raise Exception(f"No puedes inscribir materias de semestres anteriores, a menos que las hayas reprobado. La materia {subject_code} pertenece al semestre {subject_info['semester']}.")

    # Verificar si la materia ya está inscrita
    cur.execute("""
        SELECT * FROM enrollments 
        WHERE student_id = %s AND subject_code = %s
    """, (student_id, subject_code))
    
    existing_enrollment = cur.fetchone()

    if existing_enrollment:
        cur.close()
        conn.close()
        raise Exception("Ya has inscrito esta materia previamente.")

    # Revisar los créditos actuales inscritos por el estudiante en el semestre actual
    cur.execute("""
        SELECT SUM(subjects.credits) as total_credits 
        FROM enrollments 
        JOIN subjects ON enrollments.subject_code = subjects.code 
        WHERE enrollments.student_id = %s AND subjects.semester = %s
    """, (student_id, current_semester))

    total_credits = cur.fetchone()['total_credits'] or 0

    # Obtener los créditos de la materia antes de inscribirla
    cur.execute("""
        SELECT credits FROM subjects WHERE code = %s
    """, (subject_code,))

    subject_credits = cur.fetchone()['credits']

    # Verificar si al inscribir esta materia se exceden los 18 créditos permitidos para el semestre actual
    if total_credits + subject_credits > 18:
        cur.close()
        conn.close()
        raise Exception("No puedes inscribir más materias, ya has alcanzado el límite de 18 créditos en el semestre actual.")

    # Inscribir la materia
    cur.execute("""
        INSERT INTO enrollments (student_id, subject_code, enrollment_date, status) 
        VALUES (%s, %s, NOW(), 'enrolled')
    """, (student_id, subject_code))

    conn.commit()

    # Inscribir automáticamente las materias DN CAI para el semestre actual
    enroll_dn_cai(student_id, current_semester)

    # Actualizar el total de créditos después de inscribir la materia
    cur.execute("""
        SELECT SUM(subjects.credits) as total_credits 
        FROM enrollments 
        JOIN subjects ON enrollments.subject_code = subjects.code 
        WHERE enrollments.student_id = %s AND subjects.semester = %s
    """, (student_id, current_semester))

    total_credits_after = cur.fetchone()['total_credits'] or 0
    credits_remaining = 18 - total_credits_after

    cur.close()
    conn.close()

    return {
        "message": "Materia inscrita exitosamente.",
        "total_credits": total_credits_after,
        "credits_remaining": credits_remaining
    }

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
