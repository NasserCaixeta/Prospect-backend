from fastapi import APIRouter

from app.api.routes import auth, dashboard, leads, search_jobs, settings, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(leads.router)
api_router.include_router(search_jobs.router)
api_router.include_router(dashboard.router)
api_router.include_router(settings.router)
