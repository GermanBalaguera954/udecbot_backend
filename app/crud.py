#crud.py

from psycopg2 import DatabaseError
from .database import get_db_connection
import psycopg2

def check_first_time(student_id: int):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Consulta optimizada para verificar si hay al menos una inscripción
        cur.execute("SELECT 1 FROM enrollments WHERE student_id = %s LIMIT 1", (student_id,))
        enrollment_exists = cur.fetchone()
        
        return enrollment_exists is None  # Si no hay inscripciones, es la primera vez
    except DatabaseError as e:
        raise Exception(f"Error en la verificación del estudiante: {str(e)}")
    finally:
        if conn:
            cur.close()
            conn.close()

def enroll_dn_cai(student_id: int):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        conn.autocommit = False  # Iniciar transacción

        # Obtener el semestre actual del estudiante desde la base de datos
        cur.execute("""
            SELECT current_semester FROM students WHERE id = %s
        """, (student_id,))
        student_info = cur.fetchone()

        if not student_info:
            raise Exception(f"No se encontró información del estudiante con ID {student_id}.")
        
        current_semester = student_info['current_semester']

        # Inscribir materias DN CAI para todos los semestres hasta current_semester
        for semester in range(1, current_semester + 1):
            cur.execute("""
                SELECT code FROM subjects 
                WHERE semester = %s AND credits = 0 AND code LIKE 'DN-%%'
            """, (semester,))
            
            dn_cai_subjects = cur.fetchall()

            for subject in dn_cai_subjects:
                cur.execute("""
                    SELECT * FROM enrollments 
                    WHERE student_id = %s AND subject_code = %s
                """, (student_id, subject['code']))
                
                existing_enrollment = cur.fetchone()

                if not existing_enrollment:
                    cur.execute("""
                        INSERT INTO enrollments (student_id, subject_code, enrollment_date, status) 
                        VALUES (%s, %s, NOW(), 'inscrito')
                    """, (student_id, subject['code']))

        conn.commit()  # Confirmar transacción solo si todo es exitoso
    except DatabaseError as e:
        conn.rollback()  # Revertir la transacción si algo falla
        raise Exception(f"Error al inscribir DN CAI: {str(e)}")
    finally:
        if conn:
            cur.close()
            conn.close()

def enroll_subject(student_id: int, subject_code: str):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        conn.autocommit = False

        # Obtener el semestre actual del estudiante
        cur.execute("""
            SELECT current_semester FROM students WHERE id = %s
        """, (student_id,))
        student_info = cur.fetchone()

        if not student_info:
            raise Exception(f"No se encontró información del estudiante con ID {student_id}.")
        
        current_semester = student_info['current_semester']

        # Verificar si el código de la materia corresponde al semestre
        cur.execute("""
            SELECT semester, requirements, credits FROM subjects WHERE code = %s
        """, (subject_code,))
        subject_info = cur.fetchone()

        if not subject_info:
            raise Exception(f"La materia con el código {subject_code} no existe.")

        # Validar si el estudiante ha cumplido los requisitos de la materia
        requirements = subject_info['requirements'].split(', ') if subject_info['requirements'] else []
        if requirements:
            requirements_clean = [req.replace('R - ', '').strip() for req in requirements]
            cur.execute("""
                SELECT subject_code FROM enrollments 
                WHERE student_id = %s AND subject_code IN %s AND status = 'aprobado'
            """, (student_id, tuple(requirements_clean)))

            approved_subjects = cur.fetchall()
            if len(approved_subjects) < len(requirements_clean):
                raise Exception(f"No puedes inscribir {subject_code} porque no has aprobado los prerrequisitos necesarios.")

            # Verificar si la materia ya está inscrita o reprobada
            cur.execute("""
                SELECT status FROM enrollments 
                WHERE student_id = %s AND subject_code = %s
            """, (student_id, subject_code))
            existing_enrollment = cur.fetchone()
    
            if existing_enrollment:
                if existing_enrollment['status'] == 'reprobado':
                    # Actualizar el estado a 'reinscrita' en lugar de crear una nueva inscripción
                    cur.execute("""
                        UPDATE enrollments
                        SET status = 'reinscrita', enrollment_date = NOW()
                        WHERE student_id = %s AND subject_code = %s
                    """, (student_id, subject_code))
                else:
                    raise Exception("Ya has inscrito esta materia previamente y no está reprobada.")
            else:
                # Inscribir la materia si no está previamente inscrita
                cur.execute("""
                    INSERT INTO enrollments (student_id, subject_code, enrollment_date, status) 
                    VALUES (%s, %s, NOW(), 'inscrito')
                """, (student_id, subject_code))
    
        # Revisar los créditos actuales inscritos por el estudiante en el semestre actual
        cur.execute("""
            SELECT SUM(subjects.credits) as total_credits 
            FROM enrollments 
            JOIN subjects ON enrollments.subject_code = subjects.code 
            WHERE enrollments.student_id = %s AND (subjects.semester = %s OR enrollments.status = 'reprobado' OR enrollments.status = 'reinscrita')
        """, (student_id, current_semester))

        total_credits = cur.fetchone()['total_credits'] or 0
        subject_credits = subject_info['credits']

        # Verificar si al inscribir esta materia se exceden los 18 créditos permitidos
        if total_credits + subject_credits > 18:
            raise Exception("No puedes inscribir más materias, ya has alcanzado el límite de 18 créditos en el semestre actual.")

        # Inscribir automáticamente las materias DN CAI para el semestre actual
        enroll_dn_cai(student_id)

        # Recalcular los créditos usados después de inscribir la materia
        cur.execute("""
            SELECT SUM(subjects.credits) as total_credits 
            FROM enrollments 
            JOIN subjects ON enrollments.subject_code = subjects.code 
            WHERE enrollments.student_id = %s 
            AND (subjects.semester = %s OR enrollments.status = 'reinscrita')
            AND enrollments.status IN ('inscrito', 'reinscrita')
        """, (student_id, current_semester))

        total_credits_after = cur.fetchone()['total_credits'] or 0
        credits_remaining = 18 - total_credits_after

        conn.commit()  # Confirmar la transacción

        # Verificar si ya no tiene créditos disponibles
        if credits_remaining == 0:
            return {
                "message": "Has alcanzado el límite de créditos permitidos para este semestre.",
                "total_credits": total_credits_after,
                "credits_remaining": credits_remaining,
                "options": ["2. Cancelar materia", "3. Listar materias", "4. Salir"]
            }

        # Devolver el mensaje de éxito con la opción de continuar inscribiendo o volver al menú
        return {
            "message": "Materia inscrita exitosamente.",
            "total_credits": total_credits_after,
            "credits_remaining": credits_remaining,
            "options": ["0. Volver al menú principal", "1. Continuar inscribiendo otra materia"]
        }

    except psycopg2.DatabaseError as e:
        conn.rollback()
        raise Exception(f"Error durante la inscripción: {str(e)}")
    finally:
        cur.close()
        conn.close()

def cancel_subject(student_id: int, subject_code: str):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        conn.autocommit = False  # Iniciar transacción

        # Obtener el semestre actual del estudiante
        cur.execute("""
            SELECT current_semester FROM students WHERE id = %s
        """, (student_id,))
        student_info = cur.fetchone()

        if not student_info:
            raise Exception(f"No se encontró información del estudiante con ID {student_id}.")

        current_semester = student_info['current_semester']

        # Obtener información de la materia
        cur.execute("""
            SELECT semester FROM subjects WHERE code = %s
        """, (subject_code,))
        subject_info = cur.fetchone()

        if not subject_info:
            raise Exception(f"La materia con el código {subject_code} no existe.")

        # Verificar si la materia está inscrita o reinscrita
        cur.execute("""
            SELECT status FROM enrollments 
            WHERE student_id = %s AND subject_code = %s
        """, (student_id, subject_code))
        existing_enrollment = cur.fetchone()

        if not existing_enrollment:
            raise Exception(f"La materia {subject_code} no está inscrita para el estudiante {student_id}.")

        # Validar si la materia pertenece al semestre actual o es una reinscripción
        if subject_info['semester'] != current_semester and existing_enrollment['status'] != 'reinscrita':
            raise Exception(f"No puedes cancelar la materia {subject_code} porque no pertenece al semestre actual.")

        # Si la materia está reinscrita, actualizar el estado a "reprobado"
        if existing_enrollment['status'] == 'reinscrita':
            cur.execute("""
                UPDATE enrollments 
                SET status = 'reprobado' 
                WHERE student_id = %s AND subject_code = %s
            """, (student_id, subject_code))
        else:
            # Si la materia está inscrita, eliminar la inscripción
            cur.execute("""
                DELETE FROM enrollments 
                WHERE student_id = %s AND subject_code = %s
            """, (student_id, subject_code))

        # Recalcular los créditos restantes después de cancelar la materia
        cur.execute("""
            SELECT SUM(subjects.credits) as total_credits 
            FROM enrollments 
            JOIN subjects ON enrollments.subject_code = subjects.code 
            WHERE enrollments.student_id = %s AND subjects.semester = %s
        """, (student_id, current_semester))

        total_credits_after = cur.fetchone()['total_credits'] or 0
        credits_remaining = 18 - total_credits_after

        conn.commit()  # Confirmar la transacción

        return {
            "message": f"Materia {subject_code} cancelada exitosamente.",
            "total_credits": total_credits_after,
            "credits_remaining": credits_remaining
        }

    except psycopg2.DatabaseError as e:
        conn.rollback()
        raise Exception(f"Error al cancelar la materia: {str(e)}")
    finally:
        cur.close()
        conn.close()

def list_enrollments(student_id: int):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Obtener el semestre actual del estudiante
        cur.execute("""
            SELECT current_semester FROM students WHERE id = %s
        """, (student_id,))
        current_semester = cur.fetchone()['current_semester']

        # Actualizar materias reprobadas a 'reinscrita' si están reprobadas y en el semestre actual
        cur.execute("""
            UPDATE enrollments SET status = 'reinscrita'
            WHERE student_id = %s AND status = 'reprobado' AND subject_code IN (
                SELECT code FROM subjects WHERE semester <= %s
            )
        """, (student_id, current_semester))

        # Obtener materias inscritas o reinscritas, independientemente del semestre
        cur.execute("""
            SELECT subjects.code, subjects.name, subjects.credits, enrollments.status
            FROM enrollments 
            JOIN subjects ON enrollments.subject_code = subjects.code 
            WHERE enrollments.student_id = %s
            AND enrollments.status IN ('inscrito', 'reinscrita')
            ORDER BY subjects.code
        """, (student_id,))
        subjects = cur.fetchall()

        # Asegurarse de que solo devuelve materias que estén inscritas o reinscritas correctamente
        valid_subjects = [subject for subject in subjects if subject['status'] in ['inscrito', 'reinscrita']]
        
        if not valid_subjects:
            return {"message": "No tienes materias inscritas ni reinscritas."}

        return {"subjects": valid_subjects}

    except psycopg2.DatabaseError as e:
        raise Exception(f"Error al listar materias: {str(e)}")
    finally:
        if conn:
            cur.close()
            conn.close()

def list_used_credits(student_id: int):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Obtener el semestre actual del estudiante
        cur.execute("""
            SELECT current_semester FROM students WHERE id = %s
        """, (student_id,))
        result = cur.fetchone()
        
        if not result or result['current_semester'] is None:
            raise Exception(f"No se encontró el semestre actual para el estudiante con ID {student_id}.")

        current_semester = result['current_semester']

        # Consultar los créditos usados en el semestre actual o materias reinscritas
        cur.execute("""
            SELECT SUM(subjects.credits) as total_credits
            FROM enrollments
            JOIN subjects ON enrollments.subject_code = subjects.code
            WHERE enrollments.student_id = %s 
            AND (subjects.semester = %s OR enrollments.status = 'reinscrita')
            AND enrollments.status IN ('inscrito', 'reinscrita')
        """, (student_id, current_semester))

        total_credits = cur.fetchone()['total_credits'] or 0

        return {
            "student_id": student_id,
            "current_semester": current_semester,
            "total_credits_used": total_credits
        }

    except DatabaseError as e:
        raise Exception(f"Error al listar los créditos: {str(e)}")
    finally:
        if conn:
            cur.close()
            conn.close()
