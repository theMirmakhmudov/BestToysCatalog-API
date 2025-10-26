from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.response import base_success, BaseHTTPException, ErrorCodes
from app.core.i18n import get_lang
from app.core.deps import create_db_and_init_admin
from app.routers import auth, categories, products, orders, system

limiter = Limiter(key_func=get_remote_address)

def create_app():
    app = FastAPI(title="Toys Catalog API", version="v1", docs_url="/api/v1/docs", openapi_url="/api/v1/openapi.json")
    app.state.limiter = limiter

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        return JSONResponse(
            status_code=429,
            content={
                "success": False,
                "data": None,
                "error": {"code": ErrorCodes.RATE_LIMITED, "message": "Too many requests."},
                "meta": {"lang": get_lang(request)},
            },
        )

    @app.exception_handler(BaseHTTPException)
    async def base_exc_handler(request: Request, exc: BaseHTTPException):
        return JSONResponse(status_code=exc.status_code, content=exc.to_response(lang=get_lang(request)))

    app.include_router(system.router, prefix="/api/v1/system", tags=["System"])
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
    app.include_router(categories.router, prefix="/api/v1/categories", tags=["Categories"])
    app.include_router(products.router, prefix="/api/v1/products", tags=["Products"])
    app.include_router(orders.router, prefix="/api/v1/orders", tags=["Orders"])

    @app.on_event("startup")
    async def on_startup():
        # create tables & init admin if not exists
        await create_db_and_init_admin()

    return app

app = create_app()
