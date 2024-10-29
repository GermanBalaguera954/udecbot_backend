from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from .nlp_utils import process_nlp_and_act
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # URL del frontend de React
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserInput(BaseModel):
    message: str
    student_id: Optional[int] = None  # Permite que sea entero o None

@app.post("/chat/")
async def chat(user_input: UserInput):
    try:
        response = process_nlp_and_act(
            user_input.message,
            student_id=user_input.student_id
        )
        return response
    except Exception as e:
        print(f"Error en el servidor: {e}")  # Detalles del error para diagnóstico
        raise HTTPException(status_code=500, detail="Error al procesar la solicitud.")
