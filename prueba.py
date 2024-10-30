def enroll_student_in_subject(student_data: dict, subject_code: str = None):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        conn.autocommit = False  # Iniciar transacción

        student_id = student_data["id"]
        current_semester = student_data["current_semester"]

        if subject_code:
            # 1. Comprobar si la materia existe y pertenece al semestre correcto
            cur.execute("""
                SELECT semester, requirements, credits FROM subjects WHERE code = %s
            """, (subject_code,))
            subject_info = cur.fetchone()

            if not subject_info:
                return {"message": f"La materia con el código {subject_code} no existe."}

            if subject_info["semester"] > current_semester + 2:
                return {"message": "No puedes inscribir materias de más de dos semestres por delante del actual."}

            # 2. Validar si el estudiante cumple los requisitos necesarios
            requirements = subject_info['requirements'].split(', ') if subject_info['requirements'] else []
            if requirements:
                requirements_clean = [req.replace('R - ', '').strip() for req in requirements]
                cur.execute("""
                    SELECT subject_code FROM enrollments 
                    WHERE student_id = %s AND subject_code IN %s AND status = 'aprobado'
                """, (student_id, tuple(requirements_clean)))

                if len(cur.fetchall()) < len(requirements_clean):
                    return {"message": f"No puedes inscribir {subject_code} porque no has aprobado los prerrequisitos necesarios."}

            # 3. Verificar si la materia ya está inscrita o reprobada
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
                    return {"message": "Ya has inscrito esta materia previamente y no está reprobada."}
            else:
                # 4. Comprobar si hay créditos suficientes disponibles
                cur.execute("""
                    SELECT SUM(subjects.credits) as total_credits 
                    FROM enrollments 
                    JOIN subjects ON enrollments.subject_code = subjects.code 
                    WHERE enrollments.student_id = %s 
                    AND (subjects.semester = %s OR enrollments.status = 'reinscrita')
                    AND enrollments.status IN ('inscrito', 'reinscrita')
                """, (student_id, current_semester))
                
                total_credits_after = (cur.fetchone()['total_credits'] or 0) + subject_info['credits']
                if total_credits_after > 18:
                    return {"message": "No puedes inscribir esta materia porque excede el límite de 18 créditos."}

                # 5. Inscribir la materia si no está previamente inscrita y cumple todas las condiciones
                cur.execute("""
                    INSERT INTO enrollments (student_id, subject_code, enrollment_date, status) 
                    VALUES (%s, %s, NOW(), 'inscrito')
                """, (student_id, subject_code))
                conn.commit()

                credits_remaining = 18 - total_credits_after
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
