#crud.py

from .database import get_db_connection
import psycopg2
from psycopg2.extras import RealDictCursor

from psycopg2.extras import RealDictCursor

def get_student_info(student_id: int):
    print(f"Buscando información para student_id: {student_id}")
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)  # Usar RealDictCursor para obtener diccionarios
    try:
        # Obtener información del estudiante
        cur.execute("SELECT name, current_semester FROM students WHERE id = %s", (student_id,))
        result = cur.fetchone()
        
        if not result:
            print("No se encontró el estudiante en la base de datos.")
            return None  # Devolver None si el estudiante no existe

        name = result["name"]
        current_semester = result["current_semester"]

        # Obtener materias inscritas o reinscritas
        cur.execute("""
            SELECT subjects.code, subjects.name, enrollments.status
            FROM enrollments
            JOIN subjects ON enrollments.subject_code = subjects.code
            WHERE enrollments.student_id = %s AND enrollments.status IN ('inscrita', 'reinscrita')
        """, (student_id,))
        
        subjects = [{"code": subj["code"], "name": subj["name"], "status": subj["status"]} for subj in cur.fetchall()]

        # Obtener créditos usados en el semestre actual
        cur.execute("""
            SELECT SUM(subjects.credits) as total_credits
            FROM enrollments
            JOIN subjects ON enrollments.subject_code = subjects.code
            WHERE enrollments.student_id = %s AND enrollments.status IN ('inscrita', 'reinscrita')
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
        print(f"Error detallado al obtener la información del estudiante: {str(e)}")
        return None  # Retornar None en caso de error
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

        # Verificar los créditos ya inscritos
        cur.execute("""
            SELECT SUM(subjects.credits) as total_credits 
            FROM enrollments 
            JOIN subjects ON enrollments.subject_code = subjects.code 
            WHERE enrollments.student_id = %s 
            AND (subjects.semester = %s OR enrollments.status = 'reinscrita')
            AND enrollments.status IN ('inscrita', 'reinscrita')
        """, (student_id, current_semester))

        total_credits = cur.fetchone()['total_credits'] or 0

        # Respuesta inmediata si el estudiante ya alcanzó el límite de créditos
        if total_credits >= 18:
            return {
                "message": "No tienes más créditos disponibles para inscribir materias este semestre.",
                "total_credits": total_credits,
                "credits_remaining": 0,
                "options": ["Cancelar materia", "Listar materias", "Salir"]
            }

        # Inscribir automáticamente materias DN-CAI hasta el semestre actual
        for semester in range(1, current_semester + 1):
            cur.execute("""
                SELECT code FROM subjects 
                WHERE semester = %s AND credits = 0 AND code LIKE 'DN-CAI%%'
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
                        VALUES (%s, %s, NOW(), 'inscrita')
                    """, (student_id, subject['code']))

        # Continuar solo si hay un `subject_code` específico para inscribir
        if subject_code:
            # Comprobar si la materia existe y pertenece al semestre correcto
            cur.execute("""
                SELECT semester, requirements, credits FROM subjects WHERE code = %s
            """, (subject_code,))
            subject_info = cur.fetchone()

            if not subject_info:
                return {"message": f"La materia con el código {subject_code} no existe."}

            if subject_info["semester"] > current_semester + 2:
                return {"message": "No puedes inscribir materias de más de dos semestres por delante del actual."}

            # Validar requisitos y estado de inscripción
            requirements = subject_info['requirements'].split(', ') if subject_info['requirements'] else []
            if requirements:
                requirements_clean = [req.replace('R - ', '').strip() for req in requirements]
                cur.execute("""
                    SELECT subject_code FROM enrollments 
                    WHERE student_id = %s AND subject_code IN %s AND status = 'aprobado'
                """, (student_id, tuple(requirements_clean)))

                if len(cur.fetchall()) < len(requirements_clean):
                    return {"message": f"No puedes inscribir {subject_code} porque no has aprobado los prerrequisitos necesarios."}

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
                    conn.commit()
                    return {"message": f"La materia {subject_code} ha sido reinscrita exitosamente."}
                else:
                    return {"message": "Ya has inscrita esta materia previamente y no está reprobada."}

            # Verificar si hay créditos suficientes disponibles
            total_credits_after = total_credits + subject_info['credits']
            credits_remaining = 18 - total_credits_after

            if credits_remaining < 0:
                return {
                    "message": "No puedes inscribir esta materia porque excede el límite de 18 créditos.",
                    "total_credits": total_credits,
                    "credits_remaining": 0,
                    "options": ["Cancelar materia", "Listar materias", "Salir"]
                }

            # Inscribir la materia si cumple todas las condiciones
            cur.execute("""
                INSERT INTO enrollments (student_id, subject_code, enrollment_date, status) 
                VALUES (%s, %s, NOW(), 'inscrita')
            """, (student_id, subject_code))
            conn.commit()

            # Respuesta de confirmación
            if credits_remaining == 0:
                return {
                    "message": "Materia inscrita exitosamente.\n\nHaz alcanzado el límite de créditos permitidos para este semestre.",
                    "total_credits": total_credits_after,
                    "credits_remaining": credits_remaining,
                    "options": ["Cancelar materia", "Listar materias", "Salir"]
                }
            else:
                return {
                    "options": ["Cancelar materia", "Listar materias", "Salir"],
                    "total_credits": total_credits_after,
                    "credits_remaining": credits_remaining,
                    "message": "Materia inscrita exitosamente.\nContinuar inscribiendo otra materia."
                }

    except psycopg2.DatabaseError as e:
        if conn:
            conn.rollback()
        return {"message": f"Error en la inscripción: {str(e)}"}
    finally:
        if conn:
            cur.close()
            conn.close()

def cancel_subject(student_id: int, subject_code: str):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        conn.autocommit = False  # Iniciar transacción

        # Obtener información de la materia
        cur.execute("""
            SELECT semester, credits FROM subjects WHERE code = %s
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

        # Permitir cancelación si la materia está inscrita, independientemente del semestre
        if existing_enrollment['status'] == 'reinscrita':
            cur.execute("""
                UPDATE enrollments 
                SET status = 'reprobado' 
                WHERE student_id = %s AND subject_code = %s
            """, (student_id, subject_code))
        elif existing_enrollment['status'] == 'inscrita':
            # Eliminar la inscripción si está inscrita
            cur.execute("""
                DELETE FROM enrollments 
                WHERE student_id = %s AND subject_code = %s
            """, (student_id, subject_code))
        else:
            return {"message": f"No puedes cancelar la materia {subject_code} porque no pertenece al semestre actual y no está en estado inscrita o reinscrita."}

        # Confirmar la transacción
        conn.commit()

        # Recalcular los créditos restantes después de cancelar la materia
        cur.execute("""
            SELECT SUM(subjects.credits) as total_credits 
            FROM enrollments 
            JOIN subjects ON enrollments.subject_code = subjects.code 
            WHERE enrollments.student_id = %s 
            AND enrollments.status IN ('inscrita', 'reinscrita')
        """, (student_id,))

        total_credits_after = cur.fetchone()['total_credits'] or 0
        credits_remaining = 18 - total_credits_after

        # Mensaje de confirmación de cancelación
        return {
            "message": f"Materia {subject_code} cancelada correctamente.",
            "total_credits": total_credits_after,
            "credits_remaining": credits_remaining,
            "options": ["Cancelar otra materia", "Listar materias", "Salir"]
        }

    except psycopg2.DatabaseError as e:
        if conn:
            conn.rollback()
        return {"message": f"Error en la cancelación: {str(e)}"}
    finally:
        if conn:
            cur.close()
            conn.close()

def list_enrollments(student_id: int):
    conn = None
    try:
        conn = get_db_connection()
        if conn is None:
            raise psycopg2.DatabaseError("No se pudo establecer la conexión con la base de datos.")

        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Obtener todas las materias inscritas y reinscritas para el estudiante, sin importar el semestre
        cur.execute("""
            SELECT subjects.code, subjects.name, subjects.credits, enrollments.status
            FROM enrollments 
            JOIN subjects ON enrollments.subject_code = subjects.code 
            WHERE enrollments.student_id = %s
            AND enrollments.status IN ('inscrita', 'reinscrita')
            ORDER BY subjects.code
        """, (student_id,))
        
        subjects = cur.fetchall()

        if not subjects:
            return {
                "message": "No tienes materias inscritas ni reinscritas.",
                "total_credits": 0,
                "credits_remaining": 18,
                "options": ["Inscribir materia", "Salir"]
            }

        # Calcular créditos totales de todas las materias inscritas
        total_credits = sum(subject["credits"] for subject in subjects if subject["credits"] is not None)
        credits_remaining = 18 - total_credits

        # Construir y devolver la respuesta con todos los detalles
        response = {
            "message": "Aquí tienes tus materias inscritas:",
            "subjects": [{"code": subject["code"], "name": subject["name"], "credits": subject["credits"], "status": subject["status"]} for subject in subjects],
            "total_credits": total_credits,
            "credits_remaining": credits_remaining,
            "options": ["Inscribir otra materia", "Cancelar materia", "Salir"]
        }
        return response

    except psycopg2.DatabaseError as db_error:
        print(f"Error al acceder a la base de datos: {db_error}")
        return {"message": f"Error al listar materias: {str(db_error)}"}
    except Exception as e:
        print(f"Error inesperado al listar materias: {e}")
        return {"message": "Hubo un problema al intentar listar tus materias. Intenta nuevamente o contacta soporte."}
    finally:
        if conn:
            cur.close()
            conn.close()
