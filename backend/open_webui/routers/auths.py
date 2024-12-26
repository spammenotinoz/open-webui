import logging
import random
import string
import os
import re
import uuid
from supabase import create_client, Client
from fastapi import Request, Depends, HTTPException, status
from fastapi.responses import Response
from fastapi import APIRouter
from pydantic import BaseModel

from open_webui.apps.webui.models.auths import (
    SigninForm, SignupForm, AddUserForm, UpdateProfileForm, UpdatePasswordForm,
    UserResponse, SigninResponse, Auths, ApiKey,
)
from open_webui.apps.webui.models.users import Users
from open_webui.utils.utils import (
    get_password_hash, get_current_user, get_admin_user, create_token, create_api_key,
)
from open_webui.utils.misc import parse_duration, validate_email_format
from open_webui.utils.webhook import post_webhook
from open_webui.constants import ERROR_MESSAGES, WEBHOOK_MESSAGES
from open_webui.config import WEBUI_AUTH
from open_webui.env import (
    WEBUI_AUTH_TRUSTED_EMAIL_HEADER, WEBUI_AUTH_TRUSTED_NAME_HEADER,
)

router = APIRouter()

# Supabase client initialization
supabase_url = os.environ.get("SUPABASE_URL")
supabase_anon_key = os.environ.get("SUPABASE_ANON_KEY")
if not supabase_url or not supabase_anon_key:
    raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment variables")
supabase: Client = create_client(supabase_url, supabase_anon_key)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.get("/", response_model=UserResponse)
async def get_session_user(
    request: Request,
    response: Response,
    user=Depends(get_current_user)
):
    token = create_token(
        data={"id": user.id},
        expires_delta=parse_duration(request.app.state.config.JWT_EXPIRES_IN),
    )
    response.set_cookie(
        key="token",
        value=token,
        httponly=True,
    )
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "profile_image_url": user.profile_image_url,
    }

@router.post("/update/profile", response_model=UserResponse)
async def update_profile(
    form_data: UpdateProfileForm,
    session_user=Depends(get_current_user)
):
    if session_user:
        user = Users.update_user_by_id(
            session_user.id,
            {"profile_image_url": form_data.profile_image_url, "name": form_data.name},
        )
        if user:
            return user
        else:
            raise HTTPException(400, detail=ERROR_MESSAGES.DEFAULT())
    else:
        raise HTTPException(400, detail=ERROR_MESSAGES.INVALID_CRED)

@router.post("/update/password", response_model=bool)
async def update_password(
    form_data: UpdatePasswordForm,
    session_user=Depends(get_current_user)
):
    if WEBUI_AUTH_TRUSTED_EMAIL_HEADER:
        raise HTTPException(400, detail=ERROR_MESSAGES.ACTION_PROHIBITED)
    if session_user:
        user = Auths.authenticate_user(session_user.email, form_data.password)
        if user:
            hashed = get_password_hash(form_data.new_password)
            return Auths.update_user_password_by_id(user.id, hashed)
        else:
            raise HTTPException(400, detail=ERROR_MESSAGES.INVALID_PASSWORD)
    else:
        raise HTTPException(400, detail=ERROR_MESSAGES.INVALID_CRED)

@router.post("/signin", response_model=SigninResponse)
async def signin(request: Request, response: Response, form_data: SigninForm):
    try:
        logger.info(f"Attempting to sign in user: {form_data.email}")
        logger.info(f"Supabase URL: {supabase_url}")
        logger.info(f"Supabase Anon Key (first 10 chars): {supabase_anon_key[:10]}...")
        
        user = supabase.auth.sign_in_with_password({"email": form_data.email, "password": form_data.password})
        logger.info(f"Sign-in successful for user: {form_data.email}")
        
        if user:
            db_user = Users.get_user_by_email(form_data.email.lower())
            if not db_user:
                name = form_data.email.split('@')[0]
                random_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
                hashed_password = get_password_hash(random_password)
                db_user = Auths.insert_new_auth(
                    form_data.email.lower(),
                    hashed_password,
                    name,
                    "/user.png",
                    "user"
                )
                if not db_user:
                    raise HTTPException(500, detail=ERROR_MESSAGES.CREATE_USER_ERROR)
            
            token = create_token(
                data={"id": db_user.id},
                expires_delta=parse_duration(request.app.state.config.JWT_EXPIRES_IN),
            )
            response.set_cookie(
                key="token",
                value=token,
                httponly=True,
            )
            return {
                "token": token,
                "token_type": "Bearer",
                "id": db_user.id,
                "email": db_user.email,
                "name": db_user.name,
                "role": db_user.role,
                "profile_image_url": db_user.profile_image_url,
            }
        else:
            raise HTTPException(400, detail=ERROR_MESSAGES.INVALID_CRED)
    except Exception as e:
        logger.error(f"Error during signin: {str(e)}")
        raise HTTPException(400, detail=f"Authentication failed: {str(e)}")

# Include the rest of the functions (signup, add_user, get_admin_details, etc.) here...

@router.post("/api_key", response_model=ApiKey)
async def create_api_key_(user=Depends(get_current_user)):
    api_key = create_api_key()
    success = Users.update_user_api_key_by_id(user.id, api_key)
    if success:
        return {"api_key": api_key}
    else:
        raise HTTPException(500, detail=ERROR_MESSAGES.CREATE_API_KEY_ERROR)

@router.delete("/api_key", response_model=bool)
async def delete_api_key(user=Depends(get_current_user)):
    success = Users.update_user_api_key_by_id(user.id, None)
    return success

@router.get("/api_key", response_model=ApiKey)
async def get_api_key(user=Depends(get_current_user)):
    api_key = Users.get_user_api_key_by_id(user.id)
    if api_key:
        return {"api_key": api_key}
    else:
        raise HTTPException(404, detail=ERROR_MESSAGES.API_KEY_NOT_FOUND)