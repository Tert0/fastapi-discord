from typing import Any, Optional

from pydantic import BaseModel


class User(BaseModel):
    id: str
    username: str
    discriminator: Optional[int] = None
    global_name: Optional[str] = None
    avatar: Optional[str]
    avatar_url: Optional[str] = None
    locale: str
    email: Optional[str] = None
    mfa_enabled: Optional[bool] = None
    flags: Optional[int] = None
    premium_type: Optional[int] = None
    public_flags: Optional[int] = None
    banner: Optional[str] = None
    accent_color: Optional[int] = None
    verified: Optional[bool] = None
    avatar_decoration: Optional[str] = None

    def __init__(self, **data: Any):
        super().__init__(**data)
        if self.avatar:
            self.avatar_url = f"https://cdn.discordapp.com/avatars/{self.id}/{self.avatar}.png"
        else:
            self.avatar_url = "https://cdn.discordapp.com/embed/avatars/1.png"
        if self.discriminator == 0:
            self.discriminator = None
