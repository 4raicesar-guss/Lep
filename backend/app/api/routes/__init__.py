from app.api.routes.health import router as health_router
from app.api.routes.auth import router as auth_router
from app.api.routes.analytics import router as analytics_router
from app.api.routes.combat import router as combat_router
from app.api.routes.player import router as player_router
from app.api.routes.units import router as units_router
from app.api.routes.resources import router as resources_router
from app.api.routes.formation import router as formation_router
from app.api.routes.buildings import router as buildings_router

__all__ = [
    "health_router",
    "auth_router",
    "analytics_router",
    "combat_router",
    "player_router",
    "units_router",
    "resources_router",
    "formation_router",
    "buildings_router",
]

