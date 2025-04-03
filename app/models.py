from sqlalchemy import Column, Integer, String, ForeignKey, Table, Boolean, Float
from sqlalchemy.orm import relationship
from .database import Base


enrollments = Table(
    "enrollments",
    Base.metadata,
    Column("student_id", Integer, ForeignKey("students.id"), primary_key=True),
    Column("course_id", Integer, ForeignKey("courses.id"), primary_key=True),
    Column("approved", Boolean, default=False),
    Column("payment_status", Boolean,default=False),
    Column("marks",Float,nullable=True)
)

class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    
    
class Staff(Base):
    __tablename__ = "staff"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    approved = Column(Boolean, default=False)
    

class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    years = Column(Integer, nullable=False)
    fee = Column(Integer, nullable=False)
    seats = Column(Integer, nullable=False)
    students = relationship("Student", secondary=enrollments, back_populates="courses")

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    courses = relationship("Course", secondary=enrollments, back_populates="students")

