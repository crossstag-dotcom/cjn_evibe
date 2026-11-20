import os
from django.conf import settings
from apps.store.models import Invoice
from django.core.mail import EmailMessage
from reportlab.lib import colors

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Spacer,
    Paragraph,
)

from reportlab.lib.styles import getSampleStyleSheet

from datetime import datetime

from django.core.files import File

# Invoice Service
def generate_invoice_number():

    year = datetime.now().year

    last_invoice = (
        Invoice.objects
        .filter(
            invoice_number__startswith=f"EV-{year}"
        )
        .order_by("-id")
        .first()
    )

    if last_invoice:

        last_sequence = int(
            last_invoice.invoice_number.split("-")[-1]
        )

        next_sequence = last_sequence + 1

    else:

        next_sequence = 1

    return (
        f"EV-{year}-{next_sequence:06d}"
    )


# Invoice Creation Service
def create_invoice_record(order):

    if order is None:
        raise ValueError("Order cannot be None")
    
    existing_invoice = Invoice.objects.filter(
        order=order
    ).first()

    if existing_invoice:

        return existing_invoice

    invoice = Invoice.objects.create(

        order=order,

        invoice_number=
        generate_invoice_number()

    )

    return invoice



# Invoice PDF Generation Service
def generate_invoice_pdf(invoice):

    invoice_dir = os.path.join(
        settings.MEDIA_ROOT,
        "invoices"
    )

    os.makedirs(
        invoice_dir,
        exist_ok=True
    )

    filename = (
        f"{invoice.invoice_number}.pdf"
    )

    file_path = os.path.join(
        invoice_dir,
        filename
    )

    order = invoice.order

    doc = SimpleDocTemplate(
        file_path
    )

    styles = getSampleStyleSheet()

    elements = []

    # ---------------------
    # HEADER
    # ---------------------

    elements.append(
        Paragraph(
            "EVIBE",
            styles["Title"]
        )
    )

    elements.append(
        Paragraph(
            f"Invoice Number: {invoice.invoice_number}",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            f"Order ID: {order.id}",
            styles["Normal"]
        )
    )

    elements.append(
        Spacer(1, 20)
    )

    # ---------------------
    # CUSTOMER
    # ---------------------

    elements.append(
        Paragraph(
            "Customer Details",
            styles["Heading2"]
        )
    )

    elements.append(
        Paragraph(
            f"""
            {order.customer_name}<br/>
            {order.email or ''}<br/>
            {order.phone}<br/>
            {order.address}<br/>
            {order.city} - {order.pincode}
            """,
            styles["Normal"]
        )
    )

    elements.append(
        Spacer(1, 20)
    )

    # ---------------------
    # PRODUCTS
    # ---------------------

    data = [
        [
            "Product",
            "Qty",
            "Price"
        ]
    ]

    for item in order.items.all():

        data.append(
            [
                str(item.product),
                item.quantity,
                f"₹{item.price}"
            ]
        )

    table = Table(data)

    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.black),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("GRID", (0,0), (-1,-1), 1, colors.black),
        ])
    )

    elements.append(table)

    elements.append(
        Spacer(1, 20)
    )

    # ---------------------
    # TOTALS
    # ---------------------

    totals = [
        ["Subtotal", f"₹{order.subtotal}"],
        ["Reward Discount", f"₹{order.reward_discount}"],
        ["Shipping", f"₹{order.shipping_charge}"],
        ["Total", f"₹{order.total_amount}"],
    ]

    total_table = Table(totals)

    total_table.setStyle(
        TableStyle([
            ("GRID", (0,0), (-1,-1), 1, colors.black),
        ])
    )

    elements.append(
        total_table
    )

    elements.append(
        Spacer(1, 20)
    )

    elements.append(
        Paragraph(
            f"Payment Method: {order.payment_method}",
            styles["Normal"]
        )
    )

    doc.build(elements)

    invoice.invoice_pdf.name = (
        f"invoices/{filename}"
    )

    invoice.save()

    return invoice


# Invoice Email Service
def send_invoice_email(invoice):

    order = invoice.order

    if not order.email:
        return

    email = EmailMessage(
        subject=f"EVIBE Invoice - {invoice.invoice_number}",
        body=f"""
Hi {order.customer_name},

Thank you for shopping with EVIBE.

Please find your invoice attached.

Invoice Number:
{invoice.invoice_number}

Order ID:
{order.id}

Regards,
EVIBE Team
""",
        to=[order.email]
    )

    if invoice.invoice_pdf:

        email.attach_file(
            invoice.invoice_pdf.path
        )

    email.send(
        fail_silently=False
    )

# Main Invoice Creation Workflow
def create_invoice(order):

    invoice = create_invoice_record(order)

    generate_invoice_pdf(invoice)

    send_invoice_email(invoice)

    return invoice