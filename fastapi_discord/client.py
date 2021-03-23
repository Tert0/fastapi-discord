import aiohttp
from fastapi import Request
from .models import User, Guild
from .config import DISCORD_URL, DISCORD_API_URL, DISCORD_TOKEN_URL, DISCORD_OAUTH_URL, DISCORD_OAUTH_AUTHENTICATION_URL
from .exeptions import Unauthorized, RateLimited, InvalidRequest
import re
from cachetools import TTLCache, cached
from functools import wraps

api_cache = TTLCache(maxsize=50, ttl=550)


# class DiscordOAuthSession(OAuth2Session):
#     """Session containing data for a single authorized user. Handles authorization internally.
#
#     Parameters
#     ----------
#     code:
#         Authorization code included with user request after redirect from Discord.
#     """
#
#     def __init__(self, code, client_id, client_secret, scope, redirect_uri):
#         self._discord_auth_code = code
#         self._discord_client_secret = client_secret
#         self._discord_token = None
#         self.scope = scope
#         self.redirect_uri = redirect_uri
#         super().__init__(
#             client_id=client_id,
#             scope=scope,
#             redirect_uri=redirect_uri,
#         )
#
#     async def __aenter__(self):
#         await super().__aenter__()
#
#         url = API_URL + '/oauth2/token'
#
#         self._discord_token = await self.fetch_token(
#             url,
#             code=self._discord_auth_code,
#             client_secret=self._discord_client_secret
#         )
#
#         return self
#
#     async def _discord_request(self, url_fragment, method='GET'):
#         auth = self._discord_token
#         token = auth['access_token']
#         url = API_URL + url_fragment
#         headers = {
#             'Authorization': 'Authorization: Bearer ' + token
#         }
#         async with self.request(method, url, headers=headers) as resp:
#             return await resp.json()
#
#     async def identify(self):
#         """Identify a user.
#
#         Returns
#         -------
#         :class:`fastapi_discord.models.User`
#             The user who authorized the application.
#         """
#         user = await self._discord_request('/users/@me')
#         return User(user)
#
#     async def guilds(self):
#         """Fetch a user's guild list.
#
#         Returns
#         -------
#         :class:`list`
#             The user's guild list.
#         """
#         guilds = await self._discord_request('/users/@me/guilds')
#         return [Guild(guild) for guild in guilds]
#
#     async def connections(self):
#         """Fetch a user's linked 3rd-party accounts.
#
#         Returns
#         -------
#         :class:`list`
#             The user's connections.
#         """
#         connections = await self._discord_request('/users/@me/connections')
#         return connections
#
#     async def join_guild(self, guild_id, user_id=None):
#         """Add a user to a guild.
#
#         Parameters
#         ----------
#         guild_id: :class:`int`
#             The ID of the guild to add the user to.
#         user_id: :class:`Optional[int]`
#             ID of the user, if known. If not specified, will first identify the user.
#         """
#         if not user_id:
#             user = await self.identify()
#             user_id = user['id']
#         return await self._discord_request(f'/guilds/{guild_id}/members/{user_id}', method='PUT')
#
#     async def join_group_dm(self, dm_channel_id, user_id=None):
#         """Add a user to a group DM.
#
#         Parameters
#         ----------
#         dm_channel_id: :class:`int`
#             The ID of the DM channel to add the user to.
#         user_id: :class:`Optional[int]`
#             ID of the user, if known. If not specified, will first identify the user.
#         """
#         if not user_id:
#             user = await self.identify()
#             user_id = user['id']
#         return await self._discord_request(f'/channels/{dm_channel_id}/recipients/{user_id}', method='PUT')


class DiscordOAuthClient:
    """Client for Discord Oauth2.

    Parameters
    ----------
    client_id:
        Discord application client ID.
    client_secret:
        Discord application client secret.
    redirect_uri:
        Discord application redirect URI.
    """

    def __init__(self, client_id, client_secret, redirect_uri, scopes=('identify',)):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scopes = ' '.join(scope for scope in scopes)

    @property
    def oauth_login_url(self):
        """

        Returns a Discord Login URL

        """
        client_id = f'client_id={self.client_id}'
        redirect_uri = f'redirect_uri={self.redirect_uri}'
        scopes = f'scope={self.scopes}'
        response_type = 'response_type=code'
        return f'{DISCORD_OAUTH_AUTHENTICATION_URL}?{client_id}&{redirect_uri}&{scopes}&{response_type}'

    @cached(cache=api_cache)
    async def request(self, route, token=None, method='GET'):
        if token:
            headers = {
                "Authorization": f'Bearer {token}'
            }
        resp = None
        if method == 'GET':
            async with aiohttp.ClientSession() as session:
                resp = await session.get(f'{DISCORD_API_URL}{route}', headers=headers)
                data = await resp.json()
        if method == 'POST':
            async with aiohttp.ClientSession() as session:
                resp = await session.post(f'{DISCORD_API_URL}{route}', headers=headers)
                data = await resp.json()
        if resp.status == 401:
            raise Unauthorized
        if resp.status == 429:
            raise RateLimited(data, resp.headers)
        return data

    async def get_access_token(self, code: str):
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "scope": self.scopes
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(DISCORD_TOKEN_URL, data=payload) as resp:
                resp = await resp.json()
                return resp.get('access_token'), resp.get('refresh_token')

    async def user(self, request: Request):
        route = '/users/@me'
        token = self.get_token(request)
        return User(await self.request(route, token))

    async def guilds(self, request: Request):
        route = '/users/@me/guilds'
        token = self.get_token(request)
        return User(await self.request(route, token))

    def get_token(self, request: Request):
        authorization_header = request.headers.get("Authorization")
        if not authorization_header:
            raise Unauthorized
        authorization_header = authorization_header.split(" ")
        if not authorization_header[0] == "Bearer" or len(authorization_header) > 2:
            raise Unauthorized

        token = authorization_header[1]
        return token

    async def isAuthenticated(self, token: str):
        route = '/oauth2/@me'
        try:
            await self.request(route, token)
            return True
        except Unauthorized:
            return False

    def requires_authorization(self, view):
        @wraps(view)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs['request']
            if not await self.isAuthenticated(self.get_token(request)):
                raise Unauthorized
            return await view(*args, **kwargs)

        return wrapper
