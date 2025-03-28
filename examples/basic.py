from contextlib import asynccontextmanager
from typing import List

from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse

from fastapi_discord import DiscordOAuthClient, RateLimited, Unauthorized, User
from fastapi_discord.exceptions import ClientSessionNotInitialized
from fastapi_discord.models import GuildPreview

discord = DiscordOAuthClient(
    "<client-id>", "<client-secret>", "<redirect-url>", ("identify", "guilds", "email")
)  # scopes


# startup is now deprecated https://fastapi.tiangolo.com/advanced/events/#alternative-events-deprecated
# use lifespan https://fastapi.tiangolo.com/advanced/events/
@asynccontextmanager
async def lifespan(_: FastAPI):
    await discord.init()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/login")
async def login():
    return {"url": discord.oauth_login_url}


@app.get("/callback")
async def callback(code: str):
    token, refresh_token = await discord.get_access_token(code)
    return {"access_token": token, "refresh_token": refresh_token}


@app.get("/authenticated", dependencies=[Depends(discord.requires_authorization)], response_model=bool)
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
    return JSONResponse({"error": "RateLimited", "retry": e.retry_after, "message": e.message}, status_code=429)


@app.exception_handler(ClientSessionNotInitialized)
async def client_session_error_handler(_, e: ClientSessionNotInitialized):
    print(e)
    return JSONResponse({"error": "Internal Error"}, status_code=500)


@app.get("/user", dependencies=[Depends(discord.requires_authorization)], response_model=User)
async def get_user(user: User = Depends(discord.user)):
    return user


@app.get("/guilds", dependencies=[Depends(discord.requires_authorization)], response_model=List[GuildPreview])
async def get_guilds(guilds: List = Depends(discord.guilds)):
    return guilds
