class User(object):
    id: str = None
    username: str
    discriminator: str
    avatar: str
    avatar_url: str
    locale: str
    email: str

    def __init__(self, payload: dict):
        self.id = payload['id']
        self.username = payload['username']
        self.discriminator = payload['discriminator']
        self.avatar = payload['avatar']
        self.avatar_url = f'https://cdn.discordapp.com/avatars/{self.id}/{self.avatar}.png'
        self.locale = payload['locale']
        if 'email' in payload:
            self.email = payload['email']
        else:
            self.email = ''

    @property
    def dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "discriminator": self.discriminator,
            "avatar": self.avatar,
            "avatar_url": self.avatar_url,
            "locale": self.locale,
            "email": self.email
        }
