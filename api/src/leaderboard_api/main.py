from fastapi import FastAPI
from mangum import Mangum
from starlette.middleware.cors import CORSMiddleware
from leaderboard_api.routes.auth import router as auth_router
from leaderboard_api.routes.user import router as user_router

from leaderboard_api.config import get_settings

get_settings()  # load the config before we get started
app = FastAPI(title="Stardew Leaderboard API")
app.include_router(auth_router)
app.include_router(user_router)

origins = [
    "http://localhost",
    "http://localhost:5173",
    "https://stardewspeedruns.net",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


handler = Mangum(app, lifespan="off", api_gateway_base_path="/api")
