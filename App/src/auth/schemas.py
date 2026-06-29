from pydantic import BaseModel, EmailStr, field_validator, Field

class UserRegister(BaseModel):
    nume: str = Field(max_length=150)
    email: EmailStr = Field(
        max_length= 150
    )
    password: str = Field(
        min_length=8,
        max_length=128
    )
    confirm_password : str = Field(
        min_length=8,
        max_length=128
    )


    @field_validator('confirm_password')
    @classmethod
    def password_match(cls, v, info):
        if 'password' in info.data and v != info.data['password']:
            raise ValueError("Parolele nu coincid!")
        return v    

        


class UserLogin(BaseModel):
    email: EmailStr = Field(
        max_length= 150
    )
    password: str = Field(
        min_length=8,
        max_length=128
    )


class UserResponse(BaseModel):
    id: int
    nume: str
    email: str


class UserPrivate(BaseModel):
    id: int
    nume: str
    email: str
    
