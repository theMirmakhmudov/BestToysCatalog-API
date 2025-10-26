from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from io import BytesIO

def generate_order_pdf(order: dict) -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(30*mm, (height-30*mm), "Toys Catalog — Order Receipt")

    c.setFont("Helvetica", 12)
    y = height - 50*mm
    for k, v in [
        ("Order ID", order["order_id"]),
        ("Status", order["status"]),
        ("Total", order["total_amount"]),
        ("Phone", order["phone_number"]),
        ("Address", order["shipping_address"]),
    ]:
        c.drawString(20*mm, y, f"{k}: {v}")
        y -= 8*mm

    y -= 6*mm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(20*mm, y, "Items:")
    y -= 8*mm
    c.setFont("Helvetica", 11)
    for item in order["items"]:
        line = f"- {item['product_name']} x{item['quantity']} = {item['subtotal']}"
        c.drawString(22*mm, y, line)
        y -= 6*mm

    c.showPage()
    c.save()
    return buffer.getvalue()
