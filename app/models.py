#models.py

from pydantic import BaseModel, Field

class EnrollRequest(BaseModel):
    student_id: int = Field(..., gt=0, description="El ID del estudiante debe ser mayor que 0")
    subject_code: str = Field(..., min_length=1, description="El código de la materia no puede estar vacío")

class CancelRequest(BaseModel):
    student_id: int = Field(..., gt=0, description="El ID del estudiante debe ser mayor que 0")
    subject_code: str = Field(..., min_length=1, description="El código de la materia no puede estar vacío")
