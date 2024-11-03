# auth.py

import bcrypt
import jwt
import os
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from .database import execute_non_query, execute_single_query
from datetime import datetime, timedelta

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")

# Definir el router para nuestros endpoints de autenticación
router = APIRouter()

class RegisterUser(BaseModel):
    name: str
    program: str
    email: str
    password: str
    current_semester: int

class LoginUser(BaseModel):
    email: str
    password: str

def create_jwt_token(user_id: int):
    expiration = datetime.utcnow() + timedelta(hours=1)
    payload = {
        "sub": user_id,
        "exp": expiration
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

@router.post("/register")
async def register(user: RegisterUser):
    print("Datos recibidos en registro:", user)
    # Verificar si el usuario ya existe
    existing_user = execute_single_query("SELECT * FROM students WHERE email = %s", (user.email,))
    if existing_user:
        raise HTTPException(status_code=400, detail="El usuario ya está registrado")

    # Encriptar la contraseña
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())

    # Insertar el nuevo usuario en la base de datos
    query = """
        INSERT INTO students (name, program, email, password, current_semester)
        VALUES (%s, %s, %s, %s, %s)
    """
    params = (user.name, user.program, user.email, hashed_password.decode('utf-8'), user.current_semester)
    execute_non_query(query, params)

    return {"message": "Usuario registrado exitosamente"}

@router.post("/login")
async def login(user: LoginUser):
    # Consulta el usuario en la base de datos
    query = "SELECT * FROM students WHERE email = %s"
    db_user = execute_single_query(query, (user.email,))
    
    if db_user is None:
        raise HTTPException(status_code=400, detail="Usuario no encontrado")

    # Verifica la contraseña
    if not bcrypt.checkpw(user.password.encode('utf-8'), db_user["password"].encode('utf-8')):
        raise HTTPException(status_code=400, detail="Contraseña incorrecta")

    # Genera el token JWT
    token_data = {
        "sub": db_user["id"],
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    token = jwt.encode(token_data, SECRET_KEY, algorithm="HS256")

    return {"access_token": token, "token_type": "bearer"}
