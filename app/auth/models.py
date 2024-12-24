from pydantic import BaseModel, EmailStr, Field,  field_validator
import re


class MUserRegister(BaseModel):
    email: EmailStr = Field(..., description='Email address')
    password: str = Field(..., min_length=5, max_length=50, description='passworrd 5 < n < 50')
    username: str = Field(..., description='username')
    first_name: str = Field(..., description='first name')
    last_name: str = Field(..., description='last name')
