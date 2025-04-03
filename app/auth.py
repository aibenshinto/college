import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, Header
from typing import Optional

SECRET_KEY = "your-secret-key-here"  
ALGORITHM = "HS256"
TOKEN_EXPIRY_MINUTES = 60

otp_store = {}

def save_otp(email: str, otp: str, expiry_minutes: int = 10):
    expires_at = datetime.utcnow() + timedelta(minutes=expiry_minutes)
    otp_store[email] = {"otp": otp, "expires_at": expires_at}
    print(f"Saved OTP for {email}: {otp}, expires at {expires_at}")

def verify_otp(email: str, otp: str, role: str) -> str:
    if email not in otp_store:
        print(f"No OTP found for {email}")
        raise HTTPException(status_code=400, detail="OTP expired or not found")
    
    stored_otp_data = otp_store[email]
    if datetime.utcnow() > stored_otp_data["expires_at"]:
        del otp_store[email]
        print(f"OTP for {email} expired")
        raise HTTPException(status_code=400, detail="OTP expired")
    
    if stored_otp_data["otp"] != otp:
        print(f"Invalid OTP for {email}: expected {stored_otp_data['otp']}, got {otp}")
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    
    token_payload = {
        "email": email,
        "role": role,
        "exp": datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRY_MINUTES)
    }
    token = jwt.encode(token_payload, SECRET_KEY, algorithm=ALGORITHM)
    del otp_store[email]
    print(f"OTP for {email} verified, JWT token created: {token}")
    return token

def get_current_user(authorization: str = Header(...)) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.split("Bearer ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("email")
        role = payload.get("role")
        if not email or not role:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"email": email, "role": role}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")