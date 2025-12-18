from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
	username: str
	email: EmailStr

class UserCreate(UserBase):
	password: str
	is_admin: bool = False

class UserRead(UserBase):
	id: int
	is_active: bool
	is_admin: bool

	class Config:
		from_attributes = True

class UserLogin(BaseModel):
	username: str
	password: str
