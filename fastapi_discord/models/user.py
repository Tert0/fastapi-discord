from typing import Any, Optional

from pydantic import BaseModel


class User(BaseModel):
    id: str
    username: str
    avatar: Optional[str]
    discriminator: str
    avatar_url: Optional[str]
    locale: str
    email: Optional[str]
    bot: Optional[bool]
    mfa_enabled: bool
    flags: int
    premium_type: Optional[int]
    public_flags: int
    global_name: str
    
    def __init__(self, **data: Any):
        super().__init__(**data)
        if self.avatar:
            self.avatar_url = f"https://cdn.discordapp.com/avatars/{self.id}/{self.avatar}.png"
        else:
            self.avatar_url = "https://cdn.discordapp.com/embed/avatars/1.png"
