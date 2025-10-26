from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.core.deps import get_db, admin_required
from app.core.response import base_success, BaseHTTPException, ErrorCodes
from app.core.pagination import page_params
from app.core.i18n import get_lang
from app.db.models.category import Category
from app.core.permissions import IsAuthenticated

router = APIRouter()

@router.post("")
def create_category(body: CategoryCreate, db: Session = Depends(get_db), admin=Depends(admin_required), request: Request=None):
    exists = db.execute(select(Category).where((Category.name_uz == body.name_uz) | (Category.name_ru == body.name_ru))).scalar_one_or_none()
    if exists:
        raise BaseHTTPException(409, ErrorCodes.DUPLICATE, "Category name already exists.")
    c = Category(name_uz=body.name_uz, name_ru=body.name_ru)
    db.add(c); db.commit(); db.refresh(c)
    lang = get_lang(request)
    name = c.name_ru if lang == "ru" else c.name_uz
    return base_success({"id": c.id, "name": name}, lang=lang)

@router.put("/{id}")
def update_category(id: int, body: CategoryUpdate, db: Session = Depends(get_db), admin=Depends(admin_required), request: Request=None):
    c = db.get(Category, id)
    if not c:
        raise BaseHTTPException(404, ErrorCodes.NOT_FOUND, "Category not found.")
    if body.name_uz: c.name_uz = body.name_uz
    if body.name_ru: c.name_ru = body.name_ru
    db.commit(); db.refresh(c)
    lang = get_lang(request)
    name = c.name_ru if lang == "ru" else c.name_uz
    return base_success({"id": c.id, "name": name}, lang=lang)

@router.delete("/{id}", status_code=204)
def delete_category(id: int, db: Session = Depends(get_db), admin=Depends(admin_required)):
    c = db.get(Category, id)
    if not c:
        raise BaseHTTPException(404, ErrorCodes.NOT_FOUND, "Category not found.")
    # In strict mode, prevent delete if products exist (left to DB FK or business rule)
    db.delete(c); db.commit()
    return

@router.get("/{id}")
def get_category(id: int, db: Session = Depends(get_db), current=Depends(IsAuthenticated), request: Request=None):
    c = db.get(Category, id)
    if not c:
        raise BaseHTTPException(404, ErrorCodes.NOT_FOUND, "Category not found.")
    lang = get_lang(request)
    name = c.name_ru if lang == "ru" else c.name_uz
    return base_success({"id": c.id, "name": name}, lang=lang)

@router.get("")
def list_categories(db: Session = Depends(get_db), current=Depends(IsAuthenticated), request: Request=None, lp: tuple[int,int]=Depends(page_params)):
    limit, offset = lp
    total = db.execute(select(func.count()).select_from(Category)).scalar()
    rows = db.execute(select(Category).offset(offset).limit(limit)).scalars().all()
    lang = get_lang(request)
    data = [{"id": c.id, "name": (c.name_ru if lang == "ru" else c.name_uz)} for c in rows]
    return base_success(data, lang=lang, pagination={"limit":limit,"offset":offset,"count":len(data),"total":total})
