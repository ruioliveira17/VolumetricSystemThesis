import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from jose.exceptions import JWTError, ExpiredSignatureError

from auth import verify_token

logger = logging.getLogger("qubic.auth")
#----------------------------------------------------      OAuth2      ----------------------------------------------------

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login",
    scheme_name="OAuth2PasswordBearer",
    auto_error=True)

def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Retrieves user token.
    """
    try:
        payload = verify_token(token)
    except ExpiredSignatureError:
        logger.warning("Expired access token")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired.")
    except JWTError:
        logger.warning("Invalid access token")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")
    
    if payload["type"] != "access":
        logger.warning("Invalid token type")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type.")

    if payload.get("scope") == "password_reset":
        logger.warning("Password reset token used for authenticated request")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This token can only be used to change the password."
        )
    
    return {"username": payload["sub"], "role": payload["role"]}

def get_password_change_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = verify_token(token)
    except ExpiredSignatureError:
        logger.warning("Expired token")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired.")
    except JWTError:
        logger.warning("Invalid token")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")

    if payload["type"] != "access":
        logger.warning("Invalid token type")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type.")

    return {
        "username": payload["sub"],
        "role": payload["role"],
        "from_reset": payload.get("scope") == "password_reset"
    }


def require_admin(user: dict = Depends(get_current_user)):
    """
    Dependency that checks if the current user has admin role. If not, it raises an HTTPException with status code 403.
    """
    if user["role"] != "admin":
        logger.warning("Unauthorized admin access attempt by user '%s'", user["username"])
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required.")
    return user