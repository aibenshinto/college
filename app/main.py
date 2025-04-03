from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from .database import engine, get_db
from .models import Base, Admin, Staff, Course, Student, enrollments
from .schemas import (
    AdminCreate, StaffCreate, LoginRequest, VerifyOTPRequest, MessageResponse,
    TokenResponse, CourseCreate, CourseResponse, StudentCreate, EnrollmentRequest,
    EnrollmentResponse, ApprovalRequest, MarksRequest, MarksResponse,
    StudentDetailsResponse, StaffResponse, StaffApprovalRequest, StaffEditRequest
)
from .otp_utils import generate_otp, send_email
from .auth import save_otp, verify_otp, get_current_user

app = FastAPI()

@app.on_event("startup")
def create_tables():
    Base.metadata.create_all(bind=engine)
    Base.registry.configure()

# Admin Endpoints
@app.post("/admin/register", response_model=MessageResponse)
def admin_register(admin: AdminCreate, db: Session = Depends(get_db)):
    existing_admin = db.query(Admin).filter(Admin.email == admin.email).first()
    if existing_admin:
        raise HTTPException(status_code=409, detail="Admin already exists")
    
    new_admin = Admin(email=admin.email, name=admin.name)
    db.add(new_admin)
    db.commit()
    return {"message": "Admin registration successful."}

@app.post("/admin/login/", response_model=MessageResponse)
def admin_login(request: LoginRequest, db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.email == request.email).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    
    new_otp = generate_otp()
    save_otp(request.email, new_otp)
    send_email(request.email, new_otp)
    return {"message": "New OTP sent to your email. Use it to log in."}

@app.post("/admin/verify-otp/", response_model=TokenResponse)
def admin_verify(request: VerifyOTPRequest, db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.email == request.email).first()
    if admin:
        if not admin:
            raise HTTPException(status_code=404, detail="Admin not found")
        
        token = verify_otp(request.email, request.otp, role="admin")
        return {"access": token}
    
    staff = db.query(Staff).filter(Staff.email == request.email).first()
    if staff:
        if not staff.approved:
            raise HTTPException(status_code=403, detail="Staff not approved by admin")
        token = verify_otp(request.email, request.otp, role="staff")
        return {"access": token}
    
    student = db.query(Student).filter(Student.email == request.email).first()
    if not student:
        raise HTTPException(status_code=404, detail="User not found")
    
    token = verify_otp(request.email, request.otp, role="student")
    return {"access": token}


# Staff Endpoints
@app.post("/register", response_model=MessageResponse)
def register(staff: StaffCreate, db: Session = Depends(get_db)):
    existing_staff = db.query(Staff).filter(Staff.email == staff.email).first()
    if existing_staff:
        raise HTTPException(status_code=409, detail="Staff already exists")
    
    new_staff = Staff(email=staff.email, name=staff.name, approved=False)
    db.add(new_staff)
    db.commit()
    return {"message": "Registration successful. Awaiting admin approval."}

@app.post("/login/", response_model=MessageResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    staff = db.query(Staff).filter(Staff.email == request.email).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    if not staff.approved:
        raise HTTPException(status_code=403, detail="Staff not approved by admin")
    
    new_otp = generate_otp()
    save_otp(request.email, new_otp)
    send_email(request.email, new_otp)
    return {"message": "New OTP sent to your email. Use it to log in."}

    

@app.post("/admin/approve-staff/", response_model=StaffResponse)
def approve_staff(approval: StaffApprovalRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized as admin")
    
    admin = db.query(Admin).filter(Admin.email == current_user["email"]).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    
    staff = db.query(Staff).filter(Staff.email == approval.staff_email).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    
    staff.approved = approval.approved
    db.commit()
    db.refresh(staff)
    return staff

@app.post("/admin/edit-staff/", response_model=StaffResponse)
def edit_staff(edit: StaffEditRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized as admin")
    
    admin = db.query(Admin).filter(Admin.email == current_user["email"]).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    
    staff = db.query(Staff).filter(Staff.email == edit.staff_email).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    
    if edit.name is not None:
        staff.name = edit.name
    if edit.new_email is not None:
        existing_staff = db.query(Staff).filter(Staff.email == edit.new_email, Staff.id != staff.id).first()
        if existing_staff:
            raise HTTPException(status_code=409, detail="New email already in use")
        staff.email = edit.new_email
    
    db.commit()
    db.refresh(staff)
    return staff

@app.post("/add-course/", response_model=CourseResponse)
def add_course(
    course: CourseCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != "staff":
        raise HTTPException(status_code=403, detail="Not authorized as staff")
    
    staff = db.query(Staff).filter(Staff.email == current_user["email"]).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    if not staff.approved:
        raise HTTPException(status_code=403, detail="Staff not approved by admin")
    
    new_course = Course(
        name=course.name,
        description=course.description,
        fee=course.fee,
        seats=course.seats,
        years=course.years
    )
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    return new_course

# Student Endpoints
@app.post("/student-register/", response_model=MessageResponse)
def student_register(student: StudentCreate, db: Session = Depends(get_db)):
    existing_student = db.query(Student).filter(Student.email == student.email).first()
    if existing_student:
        raise HTTPException(status_code=409, detail="Student already exists")
    
    new_student = Student(name=student.name, email=student.email)
    db.add(new_student)
    db.commit()
    return {"message": "Registration successful."}

@app.post("/student-login/", response_model=MessageResponse)
def student_login(request: LoginRequest, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.email == request.email).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    new_otp = generate_otp()
    save_otp(request.email, new_otp)
    send_email(request.email, new_otp)
    return {"message": "New OTP sent to your email. Use it to log in."}

@app.post("/enroll/", response_model=EnrollmentResponse)
def enroll(enrollment: EnrollmentRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user["role"] != "student":
        raise HTTPException(status_code=403, detail="Not authorized as student")
    
    student = db.query(Student).filter(Student.email == current_user["email"]).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    course = db.query(Course).filter(Course.name == enrollment.course_name).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    enrollment_exists = db.query(enrollments).filter_by(
        student_id=student.id, course_id=course.id
    ).first()
    if enrollment_exists:
        raise HTTPException(status_code=400, detail="Student already enrolled in this course")
    
    enrolled_count = db.query(enrollments).filter_by(course_id=course.id, approved=True).count()
    if enrolled_count >= course.seats:
        raise HTTPException(status_code=400, detail="No seats available in this course")
    
    db.execute(enrollments.insert().values(
        student_id=student.id,
        course_id=course.id,
        approved=False,
        payment_status=False
    ))
    db.commit()
    return {
        "student_name": student.name,
        "course_name": course.name,
        "approved": False,
        "payment_status": False
    }

@app.post("/approve-enrollment/", response_model=EnrollmentResponse)
def approve_enrollment(approval: ApprovalRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user["role"] != "staff":
        raise HTTPException(status_code=403, detail="Not authorized as staff")
    
    staff = db.query(Staff).filter(Staff.email == current_user["email"]).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    if not staff.approved:
        raise HTTPException(status_code=403, detail="Staff not approved by admin")
    
    student = db.query(Student).filter(Student.name == approval.student_name).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    course = db.query(Course).filter(Course.name == approval.course_name).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    enrollment = db.query(enrollments).filter_by(student_id=student.id, course_id=course.id).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    
    if approval.approved:
        enrolled_count = db.query(enrollments).filter_by(course_id=course.id, approved=True).count()
        if enrolled_count >= course.seats:
            raise HTTPException(status_code=400, detail="No seats available to approve this enrollment")
    
    db.execute(
        enrollments.update()
        .where(enrollments.c.student_id == student.id)
        .where(enrollments.c.course_id == course.id)
        .values(
            approved=approval.approved,
            payment_status=approval.payment_status
        )
    )
    db.commit()
    return {
        "student_name": student.name,
        "course_name": course.name,
        "approved": approval.approved,
        "payment_status": approval.payment_status
    }

@app.post("/enter-marks/", response_model=MarksResponse)
def enter_marks(marks: MarksRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user["role"] != "staff":
        raise HTTPException(status_code=403, detail="Not authorized as staff")
    
    staff = db.query(Staff).filter(Staff.email == current_user["email"]).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    if not staff.approved:
        raise HTTPException(status_code=403, detail="Staff not approved by admin")
    
    student = db.query(Student).filter(Student.name == marks.student_name).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    course = db.query(Course).filter(Course.name == marks.course_name).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    enrollment = db.query(enrollments).filter_by(
        student_id=student.id, course_id=course.id
    ).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    
    db.execute(
        enrollments.update()
        .where(enrollments.c.student_id == student.id)
        .where(enrollments.c.course_id == course.id)
        .values(marks=marks.marks)
    )
    db.commit()
    return {
        "student_name": student.name,
        "course_name": course.name,
        "approved": enrollment.approved,
        "payment_status": enrollment.payment_status,
        "marks": marks.marks
    }

@app.get("/student-details/", response_model=StudentDetailsResponse)
def get_student_details(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user["role"] != "student":
        raise HTTPException(status_code=403, detail="Not authorized as student")
    
    student = db.query(Student).filter(Student.email == current_user["email"]).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    student_enrollments = db.query(enrollments).filter_by(student_id=student.id).all()
    enrollments_list = []
    for enrollment in student_enrollments:
        course = db.query(Course).filter(Course.id == enrollment.course_id).first()
        enrollments_list.append({
            "student_name": student.name,
            "course_name": course.name,
            "approved": enrollment.approved,
            "payment_status": enrollment.payment_status,
            "marks": enrollment.marks
        })
    return {
        "name": student.name,
        "email": student.email,
        "enrollments": enrollments_list
    }

@app.get("/available-courses/", response_model=list[CourseResponse])
def get_available_courses(db: Session = Depends(get_db)):
    courses = db.query(Course).all()
    course_list = []
    for course in courses:
        approved_count = db.query(enrollments).filter_by(
            course_id=course.id, approved=True
        ).count()
        available_seats = max(0, course.seats - approved_count)
        course_list.append({
            "id": course.id,
            "name": course.name,
            "description": course.description,
            "fee": course.fee,
            "seats": course.seats,
            "available_seats": available_seats,
            "years": course.years
        })
    return course_list