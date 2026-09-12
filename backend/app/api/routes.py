from fastapi import APIRouter

from app.api.ai_routes import router as ai_router
from app.api.auth_routes import router as auth_router
from app.api.dashboard_routes import router as dashboard_router
from app.api.master_data_routes import router as master_data_router
from app.api.project_routes import router as project_router

router = APIRouter()

# One public API router, with endpoint groups separated by responsibility.
router.include_router(auth_router)
router.include_router(master_data_router)
router.include_router(project_router)
router.include_router(dashboard_router)
router.include_router(ai_router)
