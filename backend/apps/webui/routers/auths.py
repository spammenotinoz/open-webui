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
from supabase import create_client, Client

# ... (other imports remain the same)

router = APIRouter()

# Supabase client initialization
supabase: Client = create_client('https://anrakdaroezxddxvdpaw.supabase.co', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFucmFrZGFyb2V6eGRkeHZkcGF3Iiwicm9sIjoImFub24iLCJpYXQiOjE3MDc5NjIzNTEsImV4cCI6MjAyMzUzODM1MX0.zLZm6AI7gfZlzkseKNQNC6Ek_eDhruR6gnzl1Otk1F8')

# ... (other functions remain the same)

############################
# SignIn
############################

@router.post("/signin", response_model=SigninResponse)
async def signin(request: Request, response: Response, form_data: SigninForm):
    try:
        # Authenticate user with Supabase
        user = supabase.auth.sign_in_with_password({"email": form_data.email.lower(), "password": form_data.password})
        
        if user:
            # Check if user exists in our database
            db_user = Users.get_user_by_email(form_data.email.lower())
            
            if not db_user:
                # Create user in our database
                name = form_data.email.split('@')[0]  # Use email prefix as name
                random_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
                hashed_password = get_password_hash(random_password)
                
                db_user = Auths.insert_new_auth(
                    form_data.email.lower(),
                    hashed_password,
                    name,
                    None,  # profile_image_url
                    "user"  # default role
                )
            
            token = create_token(
                data={"id": db_user.id},
                expires_delta=parse_duration(request.app.state.config.JWT_EXPIRES_IN),
            )

            # Set the cookie token
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
        logging.error(f"Error during signin: {str(e)}")
        raise HTTPException(400, detail=ERROR_MESSAGES.INVALID_CRED)

# ... (SignUp and ResetPassword functions remain unchanged)
