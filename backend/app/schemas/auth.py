from typing import Optional
from pydantic import BaseModel, EmailStr, Field, model_validator
from app.schemas.user import UserResponse


class LoginRequest(BaseModel):
    username: Optional[str] = Field(None, description="Email or username for authentication")
    email: Optional[str] = Field(None, description="Email address for authentication")
    password: str = Field(..., min_length=1, description="Account password")

    @model_validator(mode="after")
    def validate_identifier(self):
        if not self.username and not self.email:
            raise ValueError("Either 'username' or 'email' must be provided.")
        if not self.username and self.email:
            self.username = self.email
        return self


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, description="Account password, minimum 6 characters")
    full_name: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class MessageResponse(BaseModel):
    message: str
    detail: Optional[str] = None

