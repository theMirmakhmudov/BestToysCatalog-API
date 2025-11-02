from fastapi import APIRouter, Depends, Request, Query, Form, File, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, or_
from app.schemas.product import ProductCreate, ProductUpdate
from app.core.deps import get_db, admin_required
from app.core.response import base_success, BaseHTTPException, ErrorCodes
from app.core.pagination import page_params
from app.core.i18n import get_lang
from app.db.models.product import Product
from app.db.models.category import Category
from app.core.permissions import IsAuthenticated
from pathlib import Path
import uuid, shutil

router = APIRouter()

UPLOAD_DIR = Path("app/static/uploads/products")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("")
async def create_product(
    name_uz: str = Form(...),
    name_ru: str = Form(...),
    price: float = Form(...),
    category_id: int = Form(...),
    description_uz: str | None = Form(None),
    description_ru: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin=Depends(admin_required),
    request: Request = None
):
    # ✅ Validatsiya
    if price < 0:
        raise BaseHTTPException(422, ErrorCodes.VALIDATION_ERROR, "Price cannot be negative.")

    cat = db.get(Category, category_id)
    if not cat:
        raise BaseHTTPException(404, ErrorCodes.NOT_FOUND, "Category not found.")

    # ✅ Faylni tekshirish
    ext = file.filename.split(".")[-1].lower()
    if ext not in ["jpg", "jpeg", "png", "webp"]:
        raise BaseHTTPException(400, ErrorCodes.VALIDATION_ERROR, "Invalid image format. Only JPG, PNG, WEBP supported.")

    # ✅ Faylni saqlash
    filename = f"{uuid.uuid4()}.{ext}"
    file_path = UPLOAD_DIR / filename

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise BaseHTTPException(500, ErrorCodes.INTERNAL_ERROR, f"File save error: {e}")

    image_url = f"/static/uploads/products/{filename}"

    # ✅ Ma’lumotni DBga yozish
    p = Product(
        name_uz=name_uz,
        name_ru=name_ru,
        description_uz=description_uz,
        description_ru=description_ru,
        price=price,
        category_id=category_id,
        image_url=image_url
    )
    db.add(p)
    db.commit()
    db.refresh(p)

    # ✅ Tilni aniqlash
    lang = get_lang(request)
    name = p.name_ru if lang == "ru" else p.name_uz
    desc = p.description_ru if lang == "ru" else p.description_uz

    return base_success(
        {
            "id": p.id,
            "name": name,
            "description": desc,
            "price": float(p.price),
            "image_url": p.image_url,
            "category_id": p.category_id,
        },
        lang=lang
    )
@router.put("/{id}")
async def update_product(
    id: int,
    name_uz: str | None = Form(None),
    name_ru: str | None = Form(None),
    price: float | None = Form(None),
    category_id: int | None = Form(None),
    description_uz: str | None = Form(None),
    description_ru: str | None = Form(None),
    file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    admin=Depends(admin_required),
    request: Request = None
):
    """🧸 Mahsulotni yangilash (ma'lumot + rasm optional)"""
    p = db.get(Product, id)
    if not p:
        raise BaseHTTPException(404, ErrorCodes.NOT_FOUND, "Product not found.")

    # 🧩 Rasm yangilash (agar yangi fayl yuborilsa)
    if file:
        ext = file.filename.split(".")[-1].lower()
        if ext not in ["jpg", "jpeg", "png", "webp"]:
            raise BaseHTTPException(400, ErrorCodes.VALIDATION_ERROR, "Invalid image format. Only JPG, PNG, WEBP supported.")

        # Eski faylni o‘chirish (agar mavjud bo‘lsa)
        if p.image_url and "static/uploads/products/" in p.image_url:
            old_path = Path("app") / p.image_url.strip("/")
            if old_path.exists():
                old_path.unlink(missing_ok=True)

        # Yangi faylni saqlash
        filename = f"{uuid.uuid4()}.{ext}"
        file_path = UPLOAD_DIR / filename
        try:
            with file_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise BaseHTTPException(500, ErrorCodes.INTERNAL_ERROR, f"File save error: {e}")

        p.image_url = f"/static/uploads/products/{filename}"

    # 🧱 Ma'lumotlarni yangilash
    updates = {
        "name_uz": name_uz,
        "name_ru": name_ru,
        "description_uz": description_uz,
        "description_ru": description_ru,
        "price": price,
        "category_id": category_id,
    }
    for key, value in updates.items():
        if value is not None:
            setattr(p, key, value)

    db.commit()
    db.refresh(p)

    lang = get_lang(request)
    return base_success({
        "id": p.id,
        "name": (p.name_ru if lang == "ru" else p.name_uz),
        "description": (p.description_ru if lang == "ru" else p.description_uz),
        "price": float(p.price),
        "image_url": p.image_url,
        "category_id": p.category_id
    }, lang=lang)

@router.delete("/{id}", status_code=204)
def delete_product(id: int, db: Session = Depends(get_db), admin=Depends(admin_required)):
    p = db.get(Product, id)
    if not p:
        raise BaseHTTPException(404, ErrorCodes.NOT_FOUND, "Product not found.")
    db.delete(p); db.commit()
    return

@router.get("/{id}")
def get_product(id: int, db: Session = Depends(get_db), current=Depends(IsAuthenticated), request: Request=None):
    p = db.get(Product, id)
    if not p:
        raise BaseHTTPException(404, ErrorCodes.NOT_FOUND, "Product not found.")
    lang = get_lang(request)
    return base_success({
        "id": p.id,
        "name": (p.name_ru if lang == "ru" else p.name_uz),
        "description": (p.description_ru if lang == "ru" else p.description_uz),
        "price": float(p.price),
        "image_url": p.image_url,
        "category_id": p.category_id
    }, lang=lang)

@router.get("")
def list_products(
    db: Session = Depends(get_db),
    current=Depends(IsAuthenticated),
    request: Request=None,
    lp: tuple[int,int]=Depends(page_params),
    category_id: int | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    q: str | None = None,
    sort: str | None = Query(None, description="Comma separated fields e.g. price,-created_at"),
):
    limit, offset = lp
    stmt = select(Product)
    conds = []
    if category_id:
        conds.append(Product.category_id == category_id)
    if min_price is not None:
        conds.append(Product.price >= min_price)
    if max_price is not None:
        conds.append(Product.price <= max_price)
    if q:
        like = f"%{q}%"
        conds.append(or_(Product.name_uz.ilike(like), Product.name_ru.ilike(like), Product.description_uz.ilike(like), Product.description_ru.ilike(like)))
    if conds:
        from sqlalchemy import and_
        stmt = stmt.where(and_(*conds))

    # Sorting
    if sort:
        from sqlalchemy import desc
        for field in [s.strip() for s in sort.split(",")]:
            if not field: continue
            desc_flag = field.startswith("-")
            fname = field[1:] if desc_flag else field
            col = getattr(Product, fname, None)
            if col is not None:
                stmt = stmt.order_by(desc(col) if desc_flag else col)

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar()
    rows = db.execute(stmt.offset(offset).limit(limit)).scalars().all()
    lang = get_lang(request)
    data = [{
        "id": p.id,
        "name": (p.name_ru if lang == "ru" else p.name_uz),
        "description": (p.description_ru if lang == "ru" else p.description_uz),
        "price": float(p.price),
        "image_url": p.image_url,
        "category_id": p.category_id
    } for p in rows]
    return base_success(data, lang=lang, pagination={"limit":limit,"offset":offset,"count":len(data),"total":total})

@router.get("/category/{category_id}")
def by_category(category_id: int, db: Session = Depends(get_db), current=Depends(IsAuthenticated), request: Request=None, lp: tuple[int,int]=Depends(page_params)):
    limit, offset = lp
    # ensure category exists
    from app.db.models.category import Category
    cat = db.get(Category, category_id)
    if not cat:
        raise BaseHTTPException(404, ErrorCodes.NOT_FOUND, "Category not found.")
    total = db.execute(select(func.count()).select_from(Product).where(Product.category_id == category_id)).scalar()
    rows = db.execute(select(Product).where(Product.category_id == category_id).offset(offset).limit(limit)).scalars().all()
    lang = get_lang(request)
    data = [{
        "id": p.id,
        "name": (p.name_ru if lang == "ru" else p.name_uz),
        "description": (p.description_ru if lang == "ru" else p.description_uz),
        "price": float(p.price),
        "image_url": p.image_url,
        "category_id": p.category_id
    } for p in rows]
    return base_success(data, lang=lang, pagination={"limit":limit,"offset":offset,"count":len(data),"total":total})
