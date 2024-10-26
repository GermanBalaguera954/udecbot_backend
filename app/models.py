from pydantic import BaseModel, Field

class BaseRequest(BaseModel):
    student_id: int = Field(..., gt=0, description="El ID del estudiante debe ser mayor que 0")
    subject_code: str = Field(..., pattern=r'^CAD\d{11}$', description="El código de la materia debe seguir el formato 'CAD' seguido de 11 dígitos")

class EnrollRequest(BaseRequest):
    pass

class CancelRequest(BaseRequest):
    pass
