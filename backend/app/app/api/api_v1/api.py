from fastapi import APIRouter

from app.api.api_v1.endpoints import token, user, business, case, file, auth, search

api_router = APIRouter()
api_router.include_router(business.router)
api_router.include_router(case.router)
api_router.include_router(file.router)
api_router.include_router(token.router)
api_router.include_router(user.router)
api_router.include_router(search.router)
# api_router.include_router(utils.router)

#Cognito
api_router.include_router(auth.router)
