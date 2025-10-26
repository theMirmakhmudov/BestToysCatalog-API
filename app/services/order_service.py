from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.db.models.product import Product
from app.db.models.order import Order, OrderItem, OrderStatus
from app.core.response import BaseHTTPException, ErrorCodes
from decimal import Decimal

def snapshot_product(p: Product, lang: str) -> dict:
    name = p.name_ru if lang == "ru" else p.name_uz
    return {"id": p.id, "name": name, "price": float(p.price), "image_url": p.image_url, "category_id": p.category_id}

def create_order(db: Session, user_id: int, shipping_address: str, phone_number: str, comment: str | None, items: list[dict], lang: str):
    if not items:
        raise BaseHTTPException(422, ErrorCodes.INVALID_ORDER, "Items cannot be empty.")
    product_ids = [i["product_id"] for i in items]
    products = {p.id: p for p in db.execute(select(Product).where(Product.id.in_(product_ids))).scalars().all()}
    order = Order(user_id=user_id, shipping_address=shipping_address, phone_number=phone_number, comment=comment)
    db.add(order); db.flush()

    total = Decimal("0.00")
    for it in items:
        p = products.get(it["product_id"])
        if not p:
            raise BaseHTTPException(404, ErrorCodes.NOT_FOUND, f"Product {it['product_id']} not found.")
        if it["quantity"] < 1:
            raise BaseHTTPException(422, ErrorCodes.INVALID_ORDER, "Quantity must be >= 1.")
        snap = snapshot_product(p, lang)
        subtotal = Decimal(str(snap["price"])) * Decimal(it["quantity"])
        db.add(OrderItem(order_id=order.id, product_snapshot=snap, quantity=it["quantity"], subtotal=subtotal))
        total += subtotal

    db.commit()
    return {"order_id": order.id, "status": order.status.value, "total_amount": float(total), "created_at": str(order.created_at)}

def order_to_dict(db: Session, order: Order, lang: str):
    items = db.execute(select(OrderItem).where(OrderItem.order_id == order.id)).scalars().all()
    total = sum([float(i.subtotal) for i in items])
    out_items = []
    for i in items:
        out_items.append({
            "product_id": i.product_snapshot["id"],
            "product_name": i.product_snapshot["name"],
            "product_price": i.product_snapshot["price"],
            "quantity": i.quantity,
            "subtotal": float(i.subtotal)
        })
    return {
        "order_id": order.id,
        "status": order.status.value,
        "total_amount": total,
        "shipping_address": order.shipping_address,
        "phone_number": order.phone_number,
        "comment": order.comment,
        "items": out_items,
        "created_at": str(order.created_at)
    }
