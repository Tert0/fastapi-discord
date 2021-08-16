[![Maintainability](https://api.codeclimate.com/v1/badges/7a4a3db15ce4062b6c93/maintainability)](https://codeclimate.com/github/Tert0/fastapi-discord/maintainability)
[![PyPI version](https://badge.fury.io/py/fastapi-discord.svg)](https://badge.fury.io/py/fastapi-discord)
[![PyPI Downloads](https://img.shields.io/pypi/dm/fastapi-discord.svg)](https://pypi.org/project/fastapi-discord)

# FastAPI Discord (OAuth)
Support for "Login with Discord"/ Discord OAuth for FastAPI.
# Install
PIP Package `fastapi-discord`
# Example
You can find the Example in `expamples/`
```py
from typing import List

from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from fastapi_discord import DiscordOAuthClient, RateLimited, Unauthorized, User
from fastapi_discord.models import GuildPreview

app = FastAPI()

discord = DiscordOAuthClient(
    "<client-id>", "<client-secret>", "<redirect-url>", ("identify", "guilds", "email")
)  # scopes


@app.get("/login")
async def login():
    return {"url": discord.oauth_login_url}


@app.get("/callback")
async def callback(code: str):
    token, refresh_token = await discord.get_access_token(code)
    return {"access_token": token, "refresh_token": refresh_token}


@app.get(
    "/authenticated",
    dependencies=[Depends(discord.requires_authorization)],
    response_model=bool,
)
async def isAuthenticated(token: str = Depends(discord.get_token)):
    try:
        auth = await discord.isAuthenticated(token)
        return auth
    except Unauthorized:
        return False


@app.exception_handler(Unauthorized)
async def unauthorized_error_handler(_, __):
    return JSONResponse({"error": "Unauthorized"}, status_code=401)


@app.exception_handler(RateLimited)
async def rate_limit_error_handler(_, e: RateLimited):
    return JSONResponse(
        {"error": "RateLimited", "retry": e.retry_after, "message": e.message},
        status_code=429,
    )


@app.get("/user", dependencies=[Depends(discord.requires_authorization)], response_model=User)
async def get_user(user: User = Depends(discord.user)):
    return user


@app.get(
    "/guilds",
    dependencies=[Depends(discord.requires_authorization)],
    response_model=List[GuildPreview],
)
async def get_guilds(guilds: List = Depends(discord.guilds)):
    return guilds
```
# Inspired by
[Starlette-Discord](https://github.com/nwunderly/starlette-discord)

[Quart-Discord-OAuth](https://github.com/Tert0/Quart-Discord-OAuth/)

[Quart-Discord](https://github.com/jnawk/quart-discord)

Thanks to @jnawk and @nwunderly
