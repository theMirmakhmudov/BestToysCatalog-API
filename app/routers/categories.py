from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryOut, CategoryListResponse
from app.schemas.base import BaseResponse
from app.core.deps import get_db, admin_required
from app.core.response import base_success, BaseHTTPException, ErrorCodes
from app.core.pagination import page_params
from app.core.i18n import get_lang
from app.db.models.category import Category

router = APIRouter()

@router.post("", response_model=BaseResponse[CategoryOut])
def create_category(body: CategoryCreate, db: Session = Depends(get_db), admin=Depends(admin_required), request: Request=None):
    exists = db.execute(select(Category).where(
        (Category.name_uz == body.name_uz) | 
        (Category.name_ru == body.name_ru) |
        (Category.name_en == body.name_en)
    )).scalar_one_or_none()
    if exists:
        raise BaseHTTPException(409, ErrorCodes.DUPLICATE, "Category name already exists.")
    c = Category(name_uz=body.name_uz, name_ru=body.name_ru, name_en=body.name_en)
    db.add(c); db.commit(); db.refresh(c)
    lang = get_lang(request)
    name = c.name_en if lang == "en" else (c.name_ru if lang == "ru" else c.name_uz)
    return base_success(CategoryOut(id=c.id, name=name, name_uz=c.name_uz, name_ru=c.name_ru, name_en=c.name_en), lang=lang)

@router.put("/{id}", response_model=BaseResponse[CategoryOut])
def update_category(id: int, body: CategoryUpdate, db: Session = Depends(get_db), admin=Depends(admin_required), request: Request=None):
    c = db.get(Category, id)
    if not c:
        raise BaseHTTPException(404, ErrorCodes.NOT_FOUND, "Category not found.")
    if body.name_uz: c.name_uz = body.name_uz
    if body.name_ru: c.name_ru = body.name_ru
    if body.name_en: c.name_en = body.name_en
    db.commit(); db.refresh(c)
    lang = get_lang(request)
    name = c.name_en if lang == "en" else (c.name_ru if lang == "ru" else c.name_uz)
    return base_success(CategoryOut(id=c.id, name=name, name_uz=c.name_uz, name_ru=c.name_ru, name_en=c.name_en), lang=lang)

@router.delete("/{id}", status_code=204)
def delete_category(id: int, db: Session = Depends(get_db), admin=Depends(admin_required)):
    c = db.get(Category, id)
    if not c:
        raise BaseHTTPException(404, ErrorCodes.NOT_FOUND, "Category not found.")
    try:
        db.delete(c)
        db.commit()
    except Exception as e:
        from sqlalchemy.exc import IntegrityError
        if isinstance(e, IntegrityError):
            db.rollback()
            raise BaseHTTPException(409, ErrorCodes.DUPLICATE, "Cannot delete category because it has related products.")
        raise e
    return

@router.get("/{id}", response_model=BaseResponse[CategoryOut])
def get_category(id: int, db: Session = Depends(get_db), request: Request=None):
    c = db.get(Category, id)
    if not c:
        raise BaseHTTPException(404, ErrorCodes.NOT_FOUND, "Category not found.")
    lang = get_lang(request)
    name = c.name_en if lang == "en" else (c.name_ru if lang == "ru" else c.name_uz)
    return base_success(CategoryOut(id=c.id, name=name, name_uz=c.name_uz, name_ru=c.name_ru, name_en=c.name_en), lang=lang)

@router.get("", response_model=BaseResponse[list[CategoryOut]])
def list_categories(db: Session = Depends(get_db), request: Request=None, lp: tuple[int,int]=Depends(page_params)):
    limit, offset = lp
    total = db.execute(select(func.count()).select_from(Category)).scalar()
    rows = db.execute(select(Category).offset(offset).limit(limit)).scalars().all()
    lang = get_lang(request)
    
    def get_name(cat):
        if lang == "en": return cat.name_en
        if lang == "ru": return cat.name_ru
        return cat.name_uz

    data = [CategoryOut(id=c.id, name=get_name(c), name_uz=c.name_uz, name_ru=c.name_ru, name_en=c.name_en) for c in rows]
    return base_success(data, lang=lang, pagination={"limit":limit,"offset":offset,"count":len(data),"total":total})
