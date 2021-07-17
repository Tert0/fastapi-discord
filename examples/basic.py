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


@app.get('/refresh')
async def refresh(refresh_token: str):
    token, refresh_token = await discord.refresh_access_token(refresh_token)
    return {
        "access_token": token,
        "refresh_token": refresh_token
    }


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
