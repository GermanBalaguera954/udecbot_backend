import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL no está definida en las variables de entorno")

    try:
        # Intentar establecer la conexión
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    except psycopg2.DatabaseError as e:
        raise Exception(f"Error al conectar con la base de datos: {e}")

def execute_query(query, params=None):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                if cursor.description:  
                    return cursor.fetchall()
    except psycopg2.Error as e:
        raise Exception(f"Error ejecutando la consulta: {e}")

def execute_non_query(query, params=None):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                conn.commit()
    except psycopg2.Error as e:
        raise Exception(f"Error ejecutando la operación: {e}")
