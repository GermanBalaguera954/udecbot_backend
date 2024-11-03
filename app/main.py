# main.py
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from .nlp_utils import process_nlp_and_act
from .auth_utils import get_current_user  # Importa la dependencia para autenticación
from fastapi.middleware.cors import CORSMiddleware
from .auth import router as auth_router  # Importa el router de autenticación

app = FastAPI()

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir las rutas de autenticación con prefijo /auth
app.include_router(auth_router, prefix="/auth")

# Modelo para la solicitud de entrada
class UserInput(BaseModel):
    message: str
    student_id: Optional[int] = None 

# Endpoint del chat con autenticación
@app.post("/chat/")
async def chat(user_input: UserInput, user_id: int = Depends(get_current_user)):
    try:
        response = process_nlp_and_act(
            user_input.message,
            student_id=user_input.student_id
        )
        return response
    except Exception as e:
        print(f"Error en el servidor: {e}")
        raise HTTPException(status_code=500, detail="Error al procesar la solicitud.")
