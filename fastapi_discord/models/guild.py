from typing import List, Optional

from pydantic import BaseModel

from .role import Role


class GuildPreview(BaseModel):
    id: str
    name: str
    icon: Optional[str] = None
    owner: bool
    permissions: int
    features: List[str]


class Guild(GuildPreview):
    owner_id: Optional[int] = None
    verification_level: Optional[int] = None
    default_message_notifications: Optional[int] = None
    roles: Optional[List[Role]] = None
