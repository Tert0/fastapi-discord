from typing import List, Optional

from pydantic import BaseModel

from .role import Role


class GuildPreview(BaseModel):
    id: str
    name: str
    icon: Optional[str]
    owner: bool
    permissions: int
    features: List[str]


class Guild(GuildPreview):
    owner_id: Optional[int]
    verification_level: Optional[int]
    default_message_notifications: Optional[int]
    roles: Optional[List[Role]]
