import aiohttp
from fastapi import Request
from .models import User, Guild
from .config import DISCORD_URL, DISCORD_API_URL, DISCORD_TOKEN_URL, DISCORD_OAUTH_URL, DISCORD_OAUTH_AUTHENTICATION_URL
from .exeptions import Unauthorized, RateLimited, InvalidRequest
import re
from aiocache import cached
from functools import wraps


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

    @cached(ttl=550)
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
        return [Guild(guild) for guild in await self.request(route, token)]

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
