# FastAPI Discord (OAuth)
Support for "Login with Discord"/ Discord OAuth for FastAPI.
# Install
PIP Package -> Coming Soon
# Example
You can find the Example in `expamples/`
```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi_discord import DiscordOAuthClient, Unauthorized, RateLimited
import uvicorn

app = FastAPI()

discord = DiscordOAuthClient("<client-id>", "<client-secret>", "<redirect-url>",
                             ("identify", "guilds", "email"))  # scopes


@app.get("/login")
async def login():
    return {
        "url": discord.oauth_login_url
    }


@app.get("/callback")
async def callback(code: str):
    token, refresh_token = await discord.get_access_token(code)
    return {
        "access_token": token,
        "refresh_token": refresh_token
    }


@app.get("/hello")
@discord.requires_authorization
async def hello(request: Request):
    return await discord.user(request)
    return f'Hello {user.username}#{user.discriminator}!'


@app.get('/authenticated')
async def auth(request: Request):
    try:
        token = discord.get_token(request)
        auth = await discord.isAuthenticated(token)
        return f'{auth}'
    except Unauthorized:
        return 'False'


@app.exception_handler(Unauthorized)
async def unauthorized_error_handler(request: Request, e: Unauthorized):
    return JSONResponse({
        "error": "Unauthorized"
    })


@app.exception_handler(RateLimited)
async def ratelimit_error_handler(request: Request, e: RateLimited):
    return JSONResponse({
        "error": "RateLimited",
        "retry": e.retry_after,
        "message": e.message
    })


@app.get("/require_auth")
@discord.requires_authorization
async def test(request: Request):
    return 'Hello!'


uvicorn.run(app, port=5000)
```
# Inspired by
[Starlette-Discord](https://github.com/nwunderly/starlette-discord)
[Quart-Discord-OAuth](https://github.com/Tert0/Quart-Discord-OAuth/)
[Quart-Discord](https://github.com/jnawk/quart-discord)

Thanks to @jnawk and @nwunderly