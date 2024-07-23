import logging

from fastapi import Request, UploadFile, File
from fastapi import Depends, HTTPException, status
from fastapi.responses import Response
from fastapi import APIRouter
from pydantic import BaseModel
import re
import uuid
import csv
import random
import string
from supabase import create_client, Client, AuthApiError

from apps.webui.models.auths import (
    SigninForm,
    SignupForm,
    AddUserForm,
    UpdateProfileForm,
    UpdatePasswordForm,
    UserResponse,
    SigninResponse,
    Auths,
    ApiKey,
)
from apps.webui.models.users import Users

from utils.utils import (
    get_password_hash,
    get_current_user,
    get_admin_user,
    create_token,
    create_api_key,
)
from utils.misc import parse_duration, validate_email_format
from utils.webhook import post_webhook
from constants import ERROR_MESSAGES, WEBHOOK_MESSAGES
from config import (
    WEBUI_AUTH,
    WEBUI_AUTH_TRUSTED_EMAIL_HEADER,
    WEBUI_AUTH_TRUSTED_NAME_HEADER
)

router = APIRouter()

# Supabase client initialization
supabase: Client = create_client('https://anrakdaroezxddxvdpaw.supabase.co', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFucmFrZGFyb2V6eGRkeHZkcGF3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MDc5NjIzNTEsImV4cCI6MjAyMzUzODM1MX0.zLZm6AI7gfZlzkseKNQNC6Ek_eDhruR6gnzl1Otk1F8')

def generate_random_password(length: int = 12) -> str:
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))

############################
# GetSessionUser
############################

@router.get("/", response_model=UserResponse)
async def get_session_user(
    request: Request, response: Response, user=Depends(get_current_user)
):
    token = create_token(
        data={"id": user.id},
        expires_delta=parse_duration(request.app.state.config.JWT_EXPIRES_IN),
    )

    # Set the cookie token
    response.set_cookie(
        key="token",
        value=token,
        httponly=True,  # Ensures the cookie is not accessible via JavaScript
    )

    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "profile_image_url": user.profile_image_url,
    }


############################
# Update Profile
############################

@router.post("/update/profile", response_model=UserResponse)
async def update_profile(
    form_data: UpdateProfileForm, session_user=Depends(get_current_user)
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


############################
# Update Password
############################

@router.post("/update/password", response_model=bool)
async def update_password(
    form_data: UpdatePasswordForm, session_user=Depends(get_current_user)
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


############################
# SignIn
############################

@router.post("/signin", response_model=SigninResponse)
async def signin(request: Request, response: Response, form_data: SigninForm):
    email = form_data.email.lower()
    password = form_data.password
    
    try:
        auth_response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if auth_response.error:
            raise HTTPException(400, detail=auth_response.error.message)
        
        user_data = auth_response.user
        user = Users.get_user_by_email(user_data.email)
        
        if not user:
            raise HTTPException(400, detail=ERROR_MESSAGES.INVALID_CRED)

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
            "token": token,
            "token_type": "Bearer",
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "profile_image_url": user.profile_image_url,
        }
    except AuthApiError as e:
        raise HTTPException(400, detail=str(e))


############################
# SignUp
############################

@router.post("/signup", response_model=SigninResponse)
async def signup(request: Request, response: Response, form_data: SignupForm):
    if not request.app.state.config.ENABLE_SIGNUP and WEBUI_AUTH:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, detail=ERROR_MESSAGES.ACCESS_PROHIBITED
        )

    if not validate_email_format(form_data.email.lower()):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail=ERROR_MESSAGES.INVALID_EMAIL_FORMAT
        )

    if Users.get_user_by_email(form_data.email.lower()):
        raise HTTPException(400, detail=ERROR_MESSAGES.EMAIL_TAKEN)

    try:
        new_password = generate_random_password()
        user_name = form_data.email.split("@")[0]
        signup_response = supabase.auth.sign_up({"email": form_data.email, "password": new_password})
        if signup_response.error:
            raise HTTPException(400, detail=signup_response.error.message)
        
        # Add user to the original database
        user = Users.insert_new_user(signup_response.user.id, form_data.email, form_data.name, role="user")

        token = create_token(
            data={"id": user.id},
            expires_delta=parse_duration(request.app.state.config.JWT_EXPIRES_IN),
        )
        response.set_cookie(
            key="token",
            value=token,
            httponly=True,
        )

        if request.app.state.config.WEBHOOK_URL:
            post_webhook(
                request.app.state.config.WEBHOOK_URL,
                WEBHOOK_MESSAGES.USER_SIGNUP(user.name),
                {
                    "action": "signup",
                    "message": WEBHOOK_MESSAGES.USER_SIGNUP(user.name),
                    "user": user.model_dump_json(exclude_none=True),
                },
            )

        return {
            "token": token,
            "token_type": "Bearer",
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "profile_image_url": user.profile_image_url,
        }
    except AuthApiError as err:
        raise HTTPException(500, detail=str(err))


############################
# AddUser
############################

@router.post("/add", response_model=SigninResponse)
async def add_user(form_data: AddUserForm, user=Depends(get_admin_user)):

    if not validate_email_format(form_data.email.lower()):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail=ERROR_MESSAGES.INVALID_EMAIL_FORMAT
        )

    if Users.get_user_by_email(form_data.email.lower()):
        raise HTTPException(400, detail=ERROR_MESSAGES.EMAIL_TAKEN)

    try:
        print(form_data)
        hashed = get_password_hash(form_data.password)
        user = Auths.insert_new_auth(
            form_data.email.lower(),
            hashed,
            form_data.name,
            form_data.profile_image_url,
            form_data.role,
        )

        if user:
            token = create_token(data={"id": user.id})
            return {
                "token": token,
                "token_type": "Bearer",
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "profile_image_url": user.profile_image_url,
            }
        else:
            raise HTTPException(500, detail=ERROR_MESSAGES.CREATE_USER_ERROR)
    except Exception as err:
        raise HTTPException(500, detail=ERROR_MESSAGES.DEFAULT(err))


############################
# GetAdminDetails
############################

@router.get("/admin/details")
async def get_admin_details(request: Request, user=Depends(get_current_user)):
    if request.app.state.config.SHOW_ADMIN_DETAILS:
        admin_email = request.app.state.config.ADMIN_EMAIL
        admin_name = None

        print(admin_email, admin_name)

        if admin_email:
            admin = Users.get_user_by_email(admin_email)
            if admin:
                admin_name = admin.name
        else:
            admin = Users.get_first_user()
            if admin:
                admin_email = admin.email
                admin_name = admin.name

        return {
            "name": admin_name,
            "email": admin_email,
        }
    else:
        raise HTTPException(400, detail=ERROR_MESSAGES.ACTION_PROHIBITED)


############################
# ToggleSignUp
############################

@router.get("/admin/config")
async def get_admin_config(request: Request, user=Depends(get_admin_user)):
    return {
        "SHOW_ADMIN_DETAILS": request.app.state.config.SHOW_ADMIN_DETAILS,
        "ENABLE_SIGNUP": request.app.state.config.ENABLE_SIGNUP,
        "DEFAULT_USER_ROLE": request.app.state.config.DEFAULT_USER_ROLE,
        "JWT_EXPIRES_IN": request.app.state.config.JWT_EXPIRES_IN,
        "ENABLE_COMMUNITY_SHARING": request.app.state.config.ENABLE_COMMUNITY_SHARING,
    }

class AdminConfig(BaseModel):
    SHOW_ADMIN_DETAILS: bool
    ENABLE_SIGNUP: bool
    DEFAULT_USER_ROLE: str
    JWT_EXPIRES_IN: str
    ENABLE_COMMUNITY_SHARING: bool

@router.post("/admin/config")
async def update_admin_config(
    request: Request, form_data: AdminConfig, user=Depends(get_admin_user)
):
    request.app.state.config.SHOW_ADMIN_DETAILS = form_data.SHOW_ADMIN_DETAILS
    request.app.state.config.ENABLE_SIGNUP = form_data.ENABLE_SIGNUP

    if form_data.DEFAULT_USER_ROLE in ["pending", "user", "admin"]:
        request.app.state.config.DEFAULT_USER_ROLE = form_data.DEFAULT_USER_ROLE

    pattern = r"^(-1|0|(-?\d+(\.\d+)?)(ms|s|m|h|d|w))$"

    # Check if the input string matches the pattern
    if re.match(pattern, form_data.JWT_EXPIRES_IN):
        request.app.state.config.JWT_EXPIRES_IN = form_data.JWT_EXPIRES_IN

    request.app.state.config.ENABLE_COMMUNITY_SHARING = (
        form_data.ENABLE_COMMUNITY_SHARING
    )

    return {
        "SHOW_ADMIN_DETAILS": request.app.state.config.SHOW_ADMIN_DETAILS,
        "ENABLE_SIGNUP": request.app.state.config.ENABLE_SIGNUP,
        "DEFAULT_USER_ROLE": request.app.state.config.DEFAULT_USER_ROLE,
        "JWT_EXPIRES_IN": request.app.state.config.JWT_EXPIRES_IN,
        "ENABLE_COMMUNITY_SHARING": request.app.state.config.ENABLE_COMMUNITY_SHARING,
    }


############################
# API Key
############################

# create api key
@router.post("/api_key", response_model=ApiKey)
async def create_api_key_(user=Depends(get_current_user)):
    api_key = create_api_key()
    success = Users.update_user_api_key_by_id(user.id, api_key)
    if success:
        return {
            "api_key": api_key,
        }
    else:
        raise HTTPException(500, detail=ERROR_MESSAGES.CREATE_API_KEY_ERROR)

# delete api key
@router.delete("/api_key", response_model=bool)
async def delete_api_key(user=Depends(get_current_user)):
    success = Users.update_user_api_key_by_id(user.id, None)
    return success

# get api key
@router.get("/api_key", response_model=ApiKey)
async def get_api_key(user=Depends(get_current_user)):
    api_key = Users.get_user_api_key_by_id(user.id)
    if api_key:
        return {
            "api_key": api_key,
        }
    else:
        raise HTTPException(404, detail=ERROR_MESSAGES.API_KEY_NOT_FOUND)
