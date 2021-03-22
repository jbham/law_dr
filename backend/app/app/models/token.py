from typing import Optional, Dict, Any
from pydantic import BaseModel


class Token(BaseModel):
    # access_token: str
    # token_type: str
    AccessToken: Optional[str] = None
    ExpiresIn: Optional[str] = None
    TokenType: Optional[str] = None
    RefreshToken: Optional[str] = None
    IdToken: Optional[str] = None
    message: Optional[str] = None
    session: Optional[str] = None


class TokenPayload(BaseModel):
    user_id: int = None
