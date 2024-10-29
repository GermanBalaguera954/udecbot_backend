#crud.py

from .database import get_db_connection
import psycopg2
from psycopg2.extras import RealDictCursor

def get_student_info(student_id: int):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)  # Usar RealDictCursor para obtener diccionarios
    try:
        # Obtener información del estudiante
        cur.execute("SELECT name, current_semester FROM students WHERE id = %s", (student_id,))
        result = cur.fetchone()
        
        if not result:
            print("No se encontró el estudiante en la base de datos.")
            return None

        name = result["name"]
        current_semester = result["current_semester"]

        # Obtener materias inscritas o reinscritas
        cur.execute("""
            SELECT subjects.code, subjects.name, enrollments.status
            FROM enrollments
            JOIN subjects ON enrollments.subject_code = subjects.code
            WHERE enrollments.student_id = %s AND enrollments.status IN ('inscrito', 'reinscrita')
        """, (student_id,))
        
        subjects = [{"code": subj["code"], "name": subj["name"], "status": subj["status"]} for subj in cur.fetchall()]

        # Obtener créditos usados en el semestre actual
        cur.execute("""
            SELECT SUM(subjects.credits) as total_credits
            FROM enrollments
            JOIN subjects ON enrollments.subject_code = subjects.code
            WHERE enrollments.student_id = %s AND enrollments.status IN ('inscrito', 'reinscrita')
        """, (student_id,))
        
        credits_used_result = cur.fetchone()
        credits_used = credits_used_result["total_credits"] if credits_used_result and credits_used_result["total_credits"] is not None else 0

        return {
            "name": name,
            "current_semester": current_semester,
            "subjects": subjects,  # Incluye el estado correctamente
            "credits_used": credits_used
        }
    except Exception as e:
        print(f"Error detallado: {str(e)}")
        return {"message": f"Error al obtener la información del estudiante: {str(e)}"}
    finally:
        cur.close()
        conn.close()

def enroll_student_in_subject(student_data: dict, subject_code: str = None):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        conn.autocommit = False  # Iniciar transacción

        # Extraer información del estudiante de los datos recibidos
        student_id = student_data["id"]
        current_semester = student_data["current_semester"]

        # Inscribir automáticamente materias DN CAI hasta el semestre actual
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
                
                if not cur.fetchone():
                    cur.execute("""
                        INSERT INTO enrollments (student_id, subject_code, enrollment_date, status) 
                        VALUES (%s, %s, NOW(), 'inscrito')
                    """, (student_id, subject['code']))

        # Continuar solo si hay un `subject_code` específico para inscribir
        if subject_code:
            # Verificar si la materia existe y es del semestre correcto
            cur.execute("""
                SELECT semester, requirements, credits FROM subjects WHERE code = %s
            """, (subject_code,))
            subject_info = cur.fetchone()

            if not subject_info:
                return {"message": f"La materia con el código {subject_code} no existe."}

            # Validación de requisitos de la materia
            requirements = subject_info['requirements'].split(', ') if subject_info['requirements'] else []
            if requirements:
                requirements_clean = [req.replace('R - ', '').strip() for req in requirements]
                cur.execute("""
                    SELECT subject_code FROM enrollments 
                    WHERE student_id = %s AND subject_code IN %s AND status = 'aprobado'
                """, (student_id, tuple(requirements_clean)))

                if len(cur.fetchall()) < len(requirements_clean):
                    return {"message": f"No puedes inscribir {subject_code} porque no has aprobado los prerrequisitos necesarios."}

            # Comprobar si la materia ya está inscrita o reprobada
            cur.execute("""
                SELECT status FROM enrollments 
                WHERE student_id = %s AND subject_code = %s
            """, (student_id, subject_code))
            existing_enrollment = cur.fetchone()

            if existing_enrollment:
                if existing_enrollment['status'] == 'reprobado':
                    cur.execute("""
                        UPDATE enrollments
                        SET status = 'reinscrita', enrollment_date = NOW()
                        WHERE student_id = %s AND subject_code = %s
                    """, (student_id, subject_code))
                else:
                    return {"message": "Ya has inscrito esta materia previamente y no está reprobada."}
            else:
                # Inscribir la materia si no está previamente inscrita
                cur.execute("""
                    INSERT INTO enrollments (student_id, subject_code, enrollment_date, status) 
                    VALUES (%s, %s, NOW(), 'inscrito')
                """, (student_id, subject_code))

            # Revisar créditos después de inscribir
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

            # Confirmar la transacción
            conn.commit()

            # Respuesta según el límite de créditos
            if credits_remaining == 0:
                return {
                    "message": "Has alcanzado el límite de créditos permitidos para este semestre.",
                    "total_credits": total_credits_after,
                    "credits_remaining": credits_remaining,
                    "options": ["Cancelar materia", "Listar materias", "Salir"]
                }
            else:
                return {
                    "message": "Materia inscrita exitosamente.",
                    "total_credits": total_credits_after,
                    "credits_remaining": credits_remaining,
                    "options": ["Volver al menú principal", "Continuar inscribiendo otra materia"]
                }

    except psycopg2.DatabaseError as e:
        if conn:
            conn.rollback()
        return {"message": f"Error en la inscripción: {str(e)}"}
    finally:
        if conn:
            cur.close()
            conn.close()

def cancel_subject(student_id: int, subject_code: str, current_semester: int):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        conn.autocommit = False  # Iniciar transacción

        # Obtener información de la materia
        cur.execute("""
            SELECT semester FROM subjects WHERE code = %s
        """, (subject_code,))
        subject_info = cur.fetchone()

        if not subject_info:
            return {"message": f"La materia con el código {subject_code} no existe."}

        # Verificar si la materia está inscrita o reinscrita
        cur.execute("""
            SELECT status FROM enrollments 
            WHERE student_id = %s AND subject_code = %s
        """, (student_id, subject_code))
        existing_enrollment = cur.fetchone()

        if not existing_enrollment:
            return {"message": f"La materia {subject_code} no está inscrita para el estudiante {student_id}."}

        # Validar si la materia pertenece al semestre actual o es una reinscripción
        if subject_info['semester'] != current_semester and existing_enrollment['status'] != 'reinscrita':
            return {"message": f"No puedes cancelar la materia {subject_code} porque no pertenece al semestre actual."}

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
            "message": f"Materia {subject_code} cancelada correctamente.",
            "total_credits": total_credits_after,
            "credits_remaining": credits_remaining,
            "options": ["Inscribir otra materia", "Listar materias", "Salir"]
        }

    except psycopg2.DatabaseError as e:
        conn.rollback()
        return {"message": f"Error al cancelar la materia: {str(e)}"}
    finally:
        cur.close()
        conn.close()

def list_enrollments(student_id: int, current_semester: int = None):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Obtener materias inscritas en el semestre actual o reinscritas sin importar el semestre
        cur.execute("""
            SELECT subjects.code, subjects.name, subjects.credits, enrollments.status
            FROM enrollments 
            JOIN subjects ON enrollments.subject_code = subjects.code 
            WHERE enrollments.student_id = %s
            AND (enrollments.status = 'reinscrita' OR subjects.semester = %s)
            AND enrollments.status IN ('inscrito', 'reinscrita')
            ORDER BY subjects.code
        """, (student_id, current_semester))
        
        subjects = cur.fetchall()

        if not subjects:
            return {
                "message": "No tienes materias inscritas ni reinscritas.",
                "total_credits": 0,
                "credits_remaining": 18,
                "options": ["Inscribir materia", "Salir"]
            }

        total_credits = sum(subject["credits"] for subject in subjects if subject["credits"] is not None)
        credits_remaining = 18 - total_credits

        # Construir y devolver la respuesta
        response = {
            "message": "Aquí tienes tus materias inscritas:",
            "subjects": [{"code": subject["code"], "name": subject["name"], "credits": subject["credits"], "status": subject["status"]} for subject in subjects],
            "total_credits": total_credits,
            "credits_remaining": credits_remaining,
            "options": ["Inscribir otra materia", "Cancelar materia", "Salir"]
        }
        return response

    except psycopg2.DatabaseError as db_error:
        return {"message": f"Error al listar materias: {str(db_error)}"}
    finally:
        if conn:
            cur.close()
            conn.close()
