class Guild(object):
    id: str = None
    name: str
    icon: str
    owner: bool
    permissions: int
    features: list[str]

    def __init__(self, payload: dict):
        self.name = payload["name"]
        self.icon = payload["icon"]
        self.id = str(payload["id"])
        self.icon_url = f'https://cdn.discordapp.com/icons/{self.id}/{self.icon}.png'
        self.owner = bool(payload["owner"])
        self.permissions = payload["permissions"]
        self.features = list(payload["features"])

    @property
    def dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'icon': self.icon,
            'icon_url': self.icon_url,
            'owner': self.owner,
            'permissions': self.permissions,
            'features': self.features
        }
