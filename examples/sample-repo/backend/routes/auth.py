from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from backend.auth.middleware import authenticate_user
from backend.auth.jwt import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    role: str

@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest):
    """
    User login endpoint.
    Verifies user credentials and generates a signed JWT token.
    Returns HTTP 401 Unauthorized if authentication fails.
    """
    user = authenticate_user(credentials.username, credentials.password)
    if not user:
        # Returns 401 if user credentials do not match or user is disabled
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = create_access_token({"sub": user["username"], "user_id": user["id"], "role": user["role"]})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user["id"],
        role=user["role"]
    )

@router.get("/me")
async def get_current_user():
    """Returns currently authenticated user profile."""
    return {"message": "Authenticated user profile"}
