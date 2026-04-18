from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from app.database import supabase

router = APIRouter()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ResetPasswordRequest(BaseModel):
    email: EmailStr


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/register")
async def register(data: RegisterRequest):
    try:
        response = supabase.auth.sign_up({
            "email": data.email,
            "password": data.password,
            "options": {
                "data": {
                    "full_name": data.full_name
                }
            }
        })

        if response.user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration failed"
            )

        if response.user.identities is not None and len(response.user.identities) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email already exists. Please sign in instead."
            )

        return {
            "message": "Registration successful. Please check your email to confirm.",
            "user_id": response.user.id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login")
async def login(data: LoginRequest):
    try:
        response = supabase.auth.sign_in_with_password({
            "email": data.email,
            "password": data.password
        })

        if response.user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        if response.user.email_confirmed_at is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Please confirm your email address before signing in. Check your inbox."
            )

        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "user": {
                "id": response.user.id,
                "email": response.user.email,
                "full_name": response.user.user_metadata.get("full_name", "")
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )


@router.post("/refresh")
async def refresh_token(data: RefreshRequest):
    try:
        response = supabase.auth.refresh_session(data.refresh_token)
        if response.session is None:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail="Session expired. Please log in again.")


@router.post("/logout")
async def logout():
    try:
        supabase.auth.sign_out()
        return {"message": "Logged out successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest):
    try:
        supabase.auth.reset_password_email(data.email)
        return {"message": "Reset email sent"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/change-password")
async def change_password(request: Request):
    auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    try:
        token = auth_header.replace("Bearer ", "")
        user = supabase.auth.get_user(token)
        user_id = user.user.id
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    try:
        body = await request.json()
        new_password = body.get("new_password")
        if not new_password or len(new_password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
        supabase.auth.admin.update_user_by_id(user_id, {"password": new_password})
        return {"message": "Password changed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/delete-account")
async def delete_account(request: Request):
    auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    try:
        token = auth_header.replace("Bearer ", "")
        user = supabase.auth.get_user(token)
        user_id = user.user.id
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    try:
        # Delete all user data first
        for table in ["invoice_lines", "invoices", "expenses", "clients", "products", "profiles", "user_profiles"]:
            try:
                supabase.table(table).delete().eq("user_id", user_id).execute()
            except Exception:
                pass
        # Delete the auth user
        supabase.auth.admin.delete_user(user_id)
        return {"message": "Account deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
