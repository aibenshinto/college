from pydantic import BaseModel, EmailStr, Field


class AdminCreate(BaseModel):
    email: EmailStr
    name: str

class StaffCreate(BaseModel):
    email: EmailStr
    name: str

class LoginRequest(BaseModel):
    email: EmailStr

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str

class MessageResponse(BaseModel):
    message: str

class TokenResponse(BaseModel): 
    access: str
    
class CourseCreate(BaseModel):
    name: str
    description: str | None = None
    fee: int
    seats: int
    years: int

class CourseResponse(BaseModel):
    id: int
    name: str
    description: str | None
    fee: int = Field(..., ge=0)
    seats: int = Field(..., ge=1)
    available_seats: int | None = None
    years: int = Field(..., ge=1)
    class Config:
        from_attributes = True

class StudentCreate(BaseModel):
    email: EmailStr
    name: str

class EnrollmentRequest(BaseModel):
    course_name: str

class EnrollmentResponse(BaseModel):
    student_name: str
    course_name: str
    approved: bool
    payment_status: bool

class ApprovalRequest(BaseModel):
    student_name: str
    course_name: str
    approved: bool
    payment_status: bool
    
class MarksRequest(BaseModel):
    student_name: str
    course_name: str
    marks: float = Field(...,ge=0,le=100)

class MarksResponse(BaseModel):
    student_name: str
    course_name: str
    approved: bool
    payment_status: bool
    marks: float | None
    
class StudentDetailsResponse(BaseModel):
    name: str
    email: EmailStr
    enrollments: list[MarksResponse]
    
class StaffResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    approved: bool
    class Config:
        from_attributes = True

class StaffApprovalRequest(BaseModel):
    staff_email: EmailStr
    approved: bool

class StaffEditRequest(BaseModel):
    staff_email: EmailStr
    name: str | None = None
    new_email: EmailStr | None = None