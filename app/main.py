from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.staticfiles import StaticFiles
from app.core.response import BaseHTTPException, ErrorCodes
from app.core.i18n import get_lang
from app.core.deps import create_db_and_init_admin
from app.routers import auth, categories, products, orders, system, files
from fastapi.middleware.cors import CORSMiddleware

limiter = Limiter(key_func=get_remote_address)

from starlette.middleware.sessions import SessionMiddleware
from app.core.config import settings


origins = [
    "*",
]


def create_app():
    app = FastAPI(title="Toys Catalog API", version="v1", docs_url="/api/v1/docs", openapi_url="/api/v1/openapi.json")
    app.state.limiter = limiter

    @app.middleware("http")
    async def add_trace_id(request: Request, call_next):
        import uuid
        trace_id = str(uuid.uuid4())
        request.state.trace_id = trace_id
        response = await call_next(request)
        # response.headers["X-Trace-Id"] = trace_id # Optional
        return response

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        trace_id = getattr(request.state, "trace_id", None)
        return JSONResponse(
            status_code=429,
            content={
                "success": False,
                "data": None,
                "error": {"code": ErrorCodes.RATE_LIMITED, "message": "Too many requests."},
                "meta": {"lang": get_lang(request), "trace_id": trace_id},
            },
        )

    @app.exception_handler(BaseHTTPException)
    async def base_exc_handler(request: Request, exc: BaseHTTPException):
        trace_id = getattr(request.state, "trace_id", None)
        return JSONResponse(status_code=exc.status_code, content=exc.to_response(lang=get_lang(request), trace_id=trace_id))

    from sqlalchemy.exc import IntegrityError
    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        trace_id = getattr(request.state, "trace_id", None)
        return JSONResponse(
            status_code=409,
            content={
                "success": False,
                "data": None,
                "error": {"code": ErrorCodes.DUPLICATE, "message": "Database integrity error (likely duplicate or related data).", "details": {"original_error": str(exc)}},
                "meta": {"lang": get_lang(request), "trace_id": trace_id},
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        trace_id = getattr(request.state, "trace_id", None)
        import traceback
        print(f"Unhandled error: {exc}")
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "data": None,
                "error": {"code": ErrorCodes.INTERNAL_ERROR, "message": "Internal server error.", "details": {"error": str(exc)}},
                "meta": {"lang": get_lang(request), "trace_id": trace_id},
            }
        )

    app.include_router(system.router, prefix="/api/v1/system", tags=["System"])
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
    app.include_router(files.router, prefix="/api/v1/files", tags=["Files"])
    app.include_router(categories.router, prefix="/api/v1/categories", tags=["Categories"])
    app.include_router(products.router, prefix="/api/v1/products", tags=["Products"])
    app.include_router(orders.router, prefix="/api/v1/orders", tags=["Orders"])

    @app.on_event("startup")
    async def on_startup():
        # create tables & init admin if not exists
        await create_db_and_init_admin()

    from app.db.session import engine
    from app.admin import setup_admin
    setup_admin(app, engine)

    return app

app = create_app()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
