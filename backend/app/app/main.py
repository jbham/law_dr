import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from app.api.api_v1.api import api_router
from app.core import config
from app.db.session import Session
from app.api.api_logging import logger
from fastapi.middleware.gzip import GZipMiddleware

app = FastAPI(title=config.PROJECT_NAME, openapi_url="/api/v1/openapi.json")

app.add_middleware(GZipMiddleware, minimum_size=1000)

# CORS
origins = []

# Set all CORS enabled origins
if config.BACKEND_CORS_ORIGINS:
    origins_raw = config.BACKEND_CORS_ORIGINS.split(",")
    for origin in origins_raw:
        use_origin = origin.strip()
        origins.append(use_origin)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    ),

app.include_router(api_router, prefix=config.API_V1_STR)


@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    # logger.info(request)
    request.state.db = Session()
    response = await call_next(request)
    request.state.db.close()
    return response


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)

