from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.schemas.order import OrderCreate, OrderUpdate, CancelRequest
from app.core.deps import get_db, get_current_user, admin_required
from app.core.response import base_success, BaseHTTPException, ErrorCodes
from app.core.i18n import get_lang
from app.db.models.order import Order, OrderItem, OrderStatus
from app.services.order_service import create_order, order_to_dict
from app.utils.pdf import generate_order_pdf

router = APIRouter()

@router.post("")
def create(body: OrderCreate, db: Session = Depends(get_db), user=Depends(get_current_user), request: Request=None):
    data = create_order(db, user.id, body.shipping_address, body.phone_number, body.comment, [i.model_dump() for i in body.items], get_lang(request))
    return base_success(data, lang=get_lang(request))

@router.put("/{id}")
def update(id: int, body: OrderUpdate, db: Session = Depends(get_db), admin=Depends(admin_required), request: Request=None):
    o = db.get(Order, id)
    if not o:
        raise BaseHTTPException(404, ErrorCodes.NOT_FOUND, "Order not found.")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(o, k, v)
    db.commit(); db.refresh(o)
    return base_success({"order_id": o.id, "status": o.status.value}, lang=get_lang(request))

@router.delete("/{id}", status_code=204)
def delete(id: int, db: Session = Depends(get_db), admin=Depends(admin_required)):
    o = db.get(Order, id)
    if not o:
        raise BaseHTTPException(404, ErrorCodes.NOT_FOUND, "Order not found.")
    db.delete(o); db.commit()
    return

@router.get("/{id}")
def get_one(id: int, db: Session = Depends(get_db), user=Depends(get_current_user), request: Request=None):
    o = db.get(Order, id)
    if not o:
        raise BaseHTTPException(404, ErrorCodes.NOT_FOUND, "Order not found.")
    if user.role.value != "admin" and o.user_id != user.id:
        raise BaseHTTPException(403, ErrorCodes.FORBIDDEN, "Not your order.")
    return base_success(order_to_dict(db, o, get_lang(request)), lang=get_lang(request))

@router.get("")
def list_orders(
    db: Session = Depends(get_db),
    admin=Depends(admin_required),
    request: Request=None,
    status: str | None = None,
    user_id: int | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 20, offset: int = 0, sort: str | None = None,
):
    from sqlalchemy import and_, desc
    stmt = select(Order)
    conds = []
    if status:
        conds.append(Order.status == OrderStatus(status))
    if user_id:
        conds.append(Order.user_id == user_id)
    if date_from:
        from sqlalchemy import text
        conds.append(Order.created_at >= text(f"'{date_from}'"))
    if date_to:
        from sqlalchemy import text
        conds.append(Order.created_at <= text(f"'{date_to}'"))
    if conds:
        from sqlalchemy import and_
        stmt = stmt.where(and_(*conds))
    if sort:
        for field in [s.strip() for s in sort.split(",")]:
            if not field: continue
            desc_flag = field.startswith("-"); fname = field[1:] if desc_flag else field
            col = getattr(Order, fname, None)
            if col is not None:
                stmt = stmt.order_by(desc(col) if desc_flag else col)
    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar()
    rows = db.execute(stmt.offset(offset).limit(limit)).scalars().all()
    data = [order_to_dict(db, o, get_lang(request)) for o in rows]
    return base_success(data, lang=get_lang(request), pagination={"limit":limit,"offset":offset,"count":len(data),"total":total})

@router.patch("/{id}/verify")
def verify(id: int, db: Session = Depends(get_db), admin=Depends(admin_required), request: Request=None):
    o = db.get(Order, id)
    if not o:
        raise BaseHTTPException(404, ErrorCodes.NOT_FOUND, "Order not found.")
    if o.status in {OrderStatus.cancelled, OrderStatus.done}:
        raise BaseHTTPException(422, ErrorCodes.INVALID_ORDER, "Cannot verify cancelled/done order.")
    o.status = OrderStatus.verified
    db.commit(); db.refresh(o)
    return base_success({"order_id": o.id, "status": o.status.value}, lang=get_lang(request))

@router.patch("/{id}/cancel")
def cancel(id: int, body: CancelRequest, db: Session = Depends(get_db), user=Depends(get_current_user), request: Request=None):
    o = db.get(Order, id)
    if not o:
        raise BaseHTTPException(404, ErrorCodes.NOT_FOUND, "Order not found.")
    if user.role.value != "admin" and o.user_id != user.id:
        raise BaseHTTPException(403, ErrorCodes.FORBIDDEN, "Not your order.")
    if o.status in {OrderStatus.done, OrderStatus.cancelled}:
        raise BaseHTTPException(422, ErrorCodes.INVALID_ORDER, "Cannot cancel completed/already cancelled order.")
    o.status = OrderStatus.cancelled
    o.cancel_reason = body.cancel_reason
    db.commit(); db.refresh(o)
    return base_success({"order_id": o.id, "status": o.status.value, "cancel_reason": o.cancel_reason}, lang=get_lang(request))

@router.patch("/{id}/complete")
def complete(id: int, db: Session = Depends(get_db), admin=Depends(admin_required), request: Request=None):
    o = db.get(Order, id)
    if not o:
        raise BaseHTTPException(404, ErrorCodes.NOT_FOUND, "Order not found.")
    if o.status != OrderStatus.verified:
        raise BaseHTTPException(422, ErrorCodes.INVALID_ORDER, "Only verified orders can be completed.")
    o.status = OrderStatus.done
    db.commit(); db.refresh(o)
    return base_success({"order_id": o.id, "status": o.status.value}, lang=get_lang(request))

@router.get("/{id}/receipt")
def receipt(id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    o = db.get(Order, id)
    if not o:
        raise BaseHTTPException(404, ErrorCodes.NOT_FOUND, "Order not found.")
    if user.role.value != "admin" and o.user_id != user.id:
        raise BaseHTTPException(403, ErrorCodes.FORBIDDEN, "Not your order.")
    data = order_to_dict(db, o, "uz")
    pdf = generate_order_pdf(data)
    headers = {"Content-Disposition": f'inline; filename="order_{o.id}.pdf"'}
    return Response(content=pdf, media_type="application/pdf", headers=headers)
