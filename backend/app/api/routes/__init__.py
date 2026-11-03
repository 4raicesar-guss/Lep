from app.api.routes.health import router as health_router
from app.api.routes.auth import router as auth_router
from app.api.routes.analytics import router as analytics_router
from app.api.routes.combat import router as combat_router

__all__ = ["health_router", "auth_router", "analytics_router", "combat_router"]
