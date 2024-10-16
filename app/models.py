from pydantic import BaseModel

class EnrollRequest(BaseModel):
    student_id: int
    subject_code: str
    current_semester: int

class CancelRequest(BaseModel):
    student_id: int
    subject_code: str
    current_semester: int