from fastapi import APIRouter, Depends, Request, Query, Form, File, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, or_
from app.schemas.product import ProductCreate, ProductUpdate, ProductOut, ProductListResponse
from app.schemas.base import BaseResponse
from app.core.deps import get_db, admin_required
from app.core.response import base_success, BaseHTTPException, ErrorCodes
from app.core.pagination import page_params
from app.core.i18n import get_lang
from app.db.models.product import Product
from app.db.models.category import Category
from pathlib import Path
import uuid, shutil

router = APIRouter()

UPLOAD_DIR = Path("app/static/uploads/products")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("", response_model=BaseResponse[ProductOut])
async def create_product(
    name_uz: str = Form(...),
    name_ru: str = Form(...),
    name_en: str = Form(...),
    price: float = Form(...),
    category_id: int = Form(...),
    description_uz: str | None = Form(None),
    description_ru: str | None = Form(None),
    description_en: str | None = Form(None),
    image_url: str = Form(...), # Changed to string URL as per TZ
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

    # ✅ Ma’lumotni DBga yozish
    p = Product(
        name_uz=name_uz,
        name_ru=name_ru,
        name_en=name_en,
        description_uz=description_uz,
        description_ru=description_ru,
        description_en=description_en,
        price=price,
        category_id=category_id,
        image_url=image_url
    )
    db.add(p)
    db.commit()
    db.refresh(p)

    # ✅ Tilni aniqlash
    lang = get_lang(request)
    name = p.name_en if lang == "en" else (p.name_ru if lang == "ru" else p.name_uz)
    desc = p.description_en if lang == "en" else (p.description_ru if lang == "ru" else p.description_uz)

    return base_success(
        ProductOut(
            id=p.id,
            name=name,
            name_uz=p.name_uz,
            name_ru=p.name_ru,
            name_en=p.name_en,
            description=desc,
            description_uz=p.description_uz,
            description_ru=p.description_ru,
            description_en=p.description_en,
            price=float(p.price),
            image_url=p.image_url,
            category_id=p.category_id,
        ),
        lang=lang
    )

@router.put("/{id}", response_model=BaseResponse[ProductOut])
async def update_product(
    id: int,
    name_uz: str | None = Form(None),
    name_ru: str | None = Form(None),
    name_en: str | None = Form(None),
    price: float | None = Form(None),
    category_id: int | None = Form(None),
    description_uz: str | None = Form(None),
    description_ru: str | None = Form(None),
    description_en: str | None = Form(None),
    image_url: str | None = Form(None),
    db: Session = Depends(get_db),
    admin=Depends(admin_required),
    request: Request = None
):
    """🧸 Mahsulotni yangilash"""
    p = db.get(Product, id)
    if not p:
        raise BaseHTTPException(404, ErrorCodes.NOT_FOUND, "Product not found.")

    # 🧱 Ma'lumotlarni yangilash
    updates = {
        "name_uz": name_uz,
        "name_ru": name_ru,
        "name_en": name_en,
        "description_uz": description_uz,
        "description_ru": description_ru,
        "description_en": description_en,
        "price": price,
        "category_id": category_id,
        "image_url": image_url
    }
    for key, value in updates.items():
        if value is not None:
            setattr(p, key, value)

    db.commit()
    db.refresh(p)

    lang = get_lang(request)
    return base_success(ProductOut(
        id=p.id,
        name=(p.name_en if lang == "en" else (p.name_ru if lang == "ru" else p.name_uz)),
        name_uz=p.name_uz,
        name_ru=p.name_ru,
        name_en=p.name_en,
        description=(p.description_en if lang == "en" else (p.description_ru if lang == "ru" else p.description_uz)),
        description_uz=p.description_uz,
        description_ru=p.description_ru,
        description_en=p.description_en,
        price=float(p.price),
        image_url=p.image_url,
        category_id=p.category_id
    ), lang=lang)

@router.delete("/{id}", status_code=204)
def delete_product(id: int, db: Session = Depends(get_db), admin=Depends(admin_required)):
    p = db.get(Product, id)
    if not p:
        raise BaseHTTPException(404, ErrorCodes.NOT_FOUND, "Product not found.")
    db.delete(p); db.commit()
    return

@router.get("/{id}", response_model=BaseResponse[ProductOut])
def get_product(id: int, db: Session = Depends(get_db), request: Request=None):
    p = db.get(Product, id)
    if not p:
        raise BaseHTTPException(404, ErrorCodes.NOT_FOUND, "Product not found.")
    lang = get_lang(request)
    return base_success(ProductOut(
        id=p.id,
        name=(p.name_en if lang == "en" else (p.name_ru if lang == "ru" else p.name_uz)),
        name_uz=p.name_uz,
        name_ru=p.name_ru,
        name_en=p.name_en,
        description=(p.description_en if lang == "en" else (p.description_ru if lang == "ru" else p.description_uz)),
        description_uz=p.description_uz,
        description_ru=p.description_ru,
        description_en=p.description_en,
        price=float(p.price),
        image_url=p.image_url,
        category_id=p.category_id
    ), lang=lang)

@router.get("", response_model=BaseResponse[list[ProductOut]])
def list_products(
    db: Session = Depends(get_db),
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
        conds.append(or_(
            Product.name_uz.ilike(like), 
            Product.name_ru.ilike(like), 
            Product.name_en.ilike(like),
            Product.description_uz.ilike(like), 
            Product.description_ru.ilike(like),
            Product.description_en.ilike(like)
        ))
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
    
    def get_name(p):
        if lang == "en": return p.name_en
        if lang == "ru": return p.name_ru
        return p.name_uz

    def get_desc(p):
        if lang == "en": return p.description_en
        if lang == "ru": return p.description_ru
        return p.description_uz

    data = [ProductOut(
        id=p.id,
        name=get_name(p),
        name_uz=p.name_uz,
        name_ru=p.name_ru,
        name_en=p.name_en,
        description=get_desc(p),
        description_uz=p.description_uz,
        description_ru=p.description_ru,
        description_en=p.description_en,
        price=float(p.price),
        image_url=p.image_url,
        category_id=p.category_id
    ) for p in rows]
    return base_success(data, lang=lang, pagination={"limit":limit,"offset":offset,"count":len(data),"total":total})

@router.get("/category/{category_id}", response_model=BaseResponse[list[ProductOut]])
def by_category(category_id: int, db: Session = Depends(get_db), request: Request=None, lp: tuple[int,int]=Depends(page_params)):
    limit, offset = lp
    # ensure category exists
    from app.db.models.category import Category
    cat = db.get(Category, category_id)
    if not cat:
        raise BaseHTTPException(404, ErrorCodes.NOT_FOUND, "Category not found.")
    total = db.execute(select(func.count()).select_from(Product).where(Product.category_id == category_id)).scalar()
    rows = db.execute(select(Product).where(Product.category_id == category_id).offset(offset).limit(limit)).scalars().all()
    lang = get_lang(request)
    data = [ProductOut(
        id=p.id,
        name=(p.name_en if lang == "en" else (p.name_ru if lang == "ru" else p.name_uz)),
        name_uz=p.name_uz,
        name_ru=p.name_ru,
        name_en=p.name_en,
        description=(p.description_en if lang == "en" else (p.description_ru if lang == "ru" else p.description_uz)),
        description_uz=p.description_uz,
        description_ru=p.description_ru,
        description_en=p.description_en,
        price=float(p.price),
        image_url=p.image_url,
        category_id=p.category_id
    ) for p in rows]
    return base_success(data, lang=lang, pagination={"limit":limit,"offset":offset,"count":len(data),"total":total})
