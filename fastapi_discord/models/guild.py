class Guild(object):
    id: str = None
    name: str
    icon: str
    owner: bool
    owner_id: str = None
    permissions: int
    permissions_new: int
    features: list[str]

    def __init__(self, payload: dict):
        self.name = payload["name"]
        self.icon = payload["icon"]
        self.id = str(payload["id"])
        self.owner = bool(payload["owner"])
        self.owner_id = payload["owner_id"]
        self.permissions = payload["permissions"]
        self.permissions_new = payload["permissions_new"]
        self.features = list(payload["features"])

    @property
    def dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'icon': self.icon,
            'owner': self.owner,
            'owner_id': self.owner_id,
            'permissions': self.permissions,
            'permissions_new': self.permissions_new,
            'features': self.features
        }
