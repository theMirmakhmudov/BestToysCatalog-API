from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from app.db.models.user import User, RoleEnum
from app.db.models.category import Category
from app.db.models.product import Product
from app.db.models.order import Order
from app.core.config import settings
from sqlalchemy import select
from app.db.session import SessionLocal

class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        phone_number = form.get("username")
        telegram_id = form.get("password")

        if not phone_number or not telegram_id:
            return False

        try:
            tid = int(telegram_id)
        except ValueError:
            return False

        # Validate against DB
        with SessionLocal() as db:
            user = db.execute(
                select(User).where(
                    User.phone_number == phone_number,
                    User.telegram_id == tid,
                    User.role == RoleEnum.admin
                )
            ).scalar_one_or_none()

        if user:
            request.session.update({"token": str(user.id)})
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")
        if not token:
            return False
        return True

class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.customer_name, User.phone_number, User.role, User.telegram_id]
    column_searchable_list = [User.customer_name, User.phone_number]
    icon = "fa-solid fa-user"

class CategoryAdmin(ModelView, model=Category):
    column_list = [Category.id, Category.name_uz, Category.name_ru, Category.name_en]
    icon = "fa-solid fa-list"

class ProductAdmin(ModelView, model=Product):
    column_list = [Product.id, Product.name_uz, Product.price, Product.category]
    column_searchable_list = [Product.name_uz, Product.name_ru, Product.name_en]
    icon = "fa-solid fa-box"

class OrderAdmin(ModelView, model=Order):
    column_list = [Order.id, Order.user, Order.status, Order.created_at]
    column_sortable_list = [Order.created_at, Order.id]
    column_default_sort = ("created_at", True)
    icon = "fa-solid fa-cart-shopping"

def setup_admin(app, engine):
    authentication_backend = AdminAuth(secret_key=settings.SECRET_KEY)
    admin = Admin(
        app, 
        engine, 
        authentication_backend=authentication_backend, 
        base_url="/api/v1/admin", 
        title="Toys Catalog Admin"
    )
    admin.add_view(UserAdmin)
    admin.add_view(CategoryAdmin)
    admin.add_view(ProductAdmin)
    admin.add_view(OrderAdmin)
