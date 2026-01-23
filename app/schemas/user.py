from pydantic import BaseModel

class UserBase(BaseModel):
	username: str
	email: str

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
