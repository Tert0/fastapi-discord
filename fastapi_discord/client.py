from typing import Dict, List, Optional, Tuple, Union

import aiohttp
from aiocache import cached
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing_extensions import TypedDict, Literal

from .config import DISCORD_API_URL, DISCORD_OAUTH_AUTHENTICATION_URL, DISCORD_TOKEN_URL
from .exceptions import RateLimited, ScopeMissing, Unauthorized, InvalidToken
from .models import Guild, GuildPreview, User


class RefreshTokenPayload(TypedDict):
    client_id: str
    client_secret: str
    grant_type: Literal["refresh_token"]
    refresh_token: str


class TokenGrantPayload(TypedDict):
    client_id: str
    client_secret: str
    grant_type: Literal["authorization_code"]
    code: str
    redirect_uri: str


class TokenResponse(TypedDict):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str
    scope: str


PAYLOAD = Union[TokenGrantPayload, RefreshTokenPayload]


def _tokens(resp: TokenResponse) -> Tuple[str, str]:
    """
    Extracts tokens from TokenResponse

    Parameters
    ----------
    resp: TokenResponse
        Response

    Returns
    -------
    Tuple[str, str]
        An union of access_token and refresh_token

    Raises
    ------
    InvalidToken
        If tokens are `None`

    """
    access_token, refresh_token = resp.get("access_token"), resp.get("refresh_token")
    if access_token is None or refresh_token is None:
        raise InvalidToken("Tokens can't be None")
    return access_token, refresh_token


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

    def __init__(self, client_id, client_secret, redirect_uri, scopes=("identify",)):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scopes = "%20".join(scope for scope in scopes)
        self.client_session: aiohttp.ClientSession = aiohttp.ClientSession()

    def get_oauth_login_url(self, state: Optional[str] = None):
        """

        Returns a Discord Login URL

        """
        client_id = f"client_id={self.client_id}"
        redirect_uri = f"redirect_uri={self.redirect_uri}"
        scopes = f"scope={self.scopes}"
        response_type = "response_type=code"
        state = f"&state={state}" if state else ""
        return f"{DISCORD_OAUTH_AUTHENTICATION_URL}?{client_id}&{redirect_uri}&{scopes}&{response_type}{state}"

    oauth_login_url = property(get_oauth_login_url)

    @cached(ttl=550)
    async def request(self, route: str, token: str = None, method: Literal["GET", "POST"] = "GET"):
        headers: Dict = {}
        if token:
            headers = {"Authorization": f"Bearer {token}"}
        if method == "GET":
            async with self.client_session.get(f"{DISCORD_API_URL}{route}", headers=headers) as resp:
                data = await resp.json()
        elif method == "POST":
            async with self.client_session.post(f"{DISCORD_API_URL}{route}", headers=headers) as resp:
                data = await resp.json()
        else:
            raise Exception("Other HTTP than GET and POST are currently not Supported")
        if resp.status == 401:
            raise Unauthorized
        if resp.status == 429:
            raise RateLimited(data, resp.headers)
        return data

    async def get_token_response(self, payload: PAYLOAD) -> TokenResponse:
        async with self.client_session.post(DISCORD_TOKEN_URL, data=payload) as resp:
            return await resp.json()

    async def get_access_token(self, code: str) -> Tuple[str, str]:
        payload: TokenGrantPayload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
        }
        resp = await self.get_token_response(payload)
        return _tokens(resp)

    async def refresh_access_token(self, refresh_token: str) -> Tuple[str, str]:
        payload: RefreshTokenPayload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        resp = await self.get_token_response(payload)
        return _tokens(resp)

    async def user(self, request: Request):
        if "identify" not in self.scopes:
            raise ScopeMissing("identify")
        route = "/users/@me"
        token = self.get_token(request)
        return User(**(await self.request(route, token)))

    async def guilds(self, request: Request) -> List[GuildPreview]:
        if "guilds" not in self.scopes:
            raise ScopeMissing("guilds")
        route = "/users/@me/guilds"
        token = self.get_token(request)
        return [Guild(**guild) for guild in await self.request(route, token)]

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
        route = "/oauth2/@me"
        try:
            await self.request(route, token)
            return True
        except Unauthorized:
            return False

    async def requires_authorization(self, bearer: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer())):
        if bearer is None:
            raise Unauthorized
        if not await self.isAuthenticated(bearer.credentials):
            raise Unauthorized
