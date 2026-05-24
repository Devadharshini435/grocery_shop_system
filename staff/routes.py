import MySQLdb
from flask import Response, render_template, request, redirect, url_for,session
from . import staff
from extensions import mysql
from email.message import EmailMessage
import smtplib
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from flask import make_response
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
import io
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))

EMAIL_ADDRESS = "grocerystoreproject2026@gmail.com"
EMAIL_PASSWORD = "fjxb bean vujn fnkk"



def send_status_email(to_email, order_id, order_date, status, products):

    subject = "🎉 Order Delivered"
    color = "#28a745"

    # ✅ product rows + total
    product_rows = ""

    grand_total = 0

    for product in products:

        subtotal = float(product['price']) * int(product['qty'])

        grand_total += subtotal

        product_rows += f"""

        <tr>

            <td style="
                padding:6px;
                border:1px solid #ddd;
            ">
                {product['name']}
            </td>

            <td style="
                padding:6px;
                border:1px solid #ddd;
                text-align:center;
            ">
                {product['qty']}
            </td>

            <td style="
                padding:6px;
                border:1px solid #ddd;
                text-align:right;
            ">
                ₹{product['price']}
            </td>

            <td style="
                padding:6px;
                border:1px solid #ddd;
                text-align:right;
            ">
                ₹{subtotal}
            </td>

        </tr>

        """

    msg = EmailMessage()

    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email

    msg.set_content("Your order has been delivered successfully.")

    html_content = f"""

    <html>

    <body style="
        font-family:Arial;
        background:#f4f6f8;
        padding:10px;
    ">

        <div style="
            max-width:600px;
            margin:auto;
            background:white;
            border-radius:8px;
            overflow:hidden;
            box-shadow:0 0 5px rgba(0,0,0,0.1);
        ">

            <!-- Header -->

            <div style="
                background:{color};
                color:white;
                padding:15px;
                text-align:center;
            ">

                <h2 style="margin:0;">
                    Grocery Store
                </h2>

                <h3 style="margin-top:5px;">
                    Order Delivered Successfully 🎉
                </h3>

            </div>

            <!-- Body -->

            <div style="padding:15px;">

                <p>Hello Customer,</p>

                <p>
                    Your order has been delivered successfully.
                </p>

                <!-- Order Details -->

                <table style="
                    width:100%;
                    border-collapse:collapse;
                    font-size:14px;
                ">

                    <tr>
                        <td><b>Order ID</b></td>
                        <td>#{order_id}</td>
                    </tr>

                    <tr style="background:#f2f2f2;">
                        <td><b>Order Date</b></td>
                        <td>{order_date}</td>
                    </tr>

                    <tr>
                        <td><b>Status</b></td>
                        <td style="color:{color};">
                            <b>{status}</b>
                        </td>
                    </tr>

                </table>

                <!-- Products -->

                <h3 style="margin-top:20px;">
                    Ordered Products
                </h3>

                <table style="
                    width:100%;
                    border-collapse:collapse;
                    font-size:14px;
                ">

                    <tr style="
                        background:{color};
                        color:white;
                    ">

                        <th style="
                            padding:6px;
                            border:1px solid #ddd;
                        ">
                            Product
                        </th>

                        <th style="
                            padding:6px;
                            border:1px solid #ddd;
                        ">
                            Qty
                        </th>

                        <th style="
                            padding:6px;
                            border:1px solid #ddd;
                        ">
                            Price
                        </th>

                        <th style="
                            padding:6px;
                            border:1px solid #ddd;
                        ">
                            Total
                        </th>

                    </tr>

                    {product_rows}

                    <!-- Grand Total -->

                    <tr>

                        <td colspan="3"
                            style="
                            padding:8px;
                            border:1px solid #ddd;
                            text-align:right;
                            font-weight:bold;
                            background:#f2f2f2;
                        ">

                            Grand Total

                        </td>

                        <td style="
                            padding:8px;
                            border:1px solid #ddd;
                            font-weight:bold;
                            color:{color};
                            text-align:right;
                            background:#f2f2f2;
                        ">

                            ₹{grand_total}

                        </td>

                    </tr>

                </table>

            </div>

        </div>

    </body>

    </html>

    """

    msg.add_alternative(html_content, subtype="html")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:

        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

        server.send_message(msg)

@staff.route("/staff/login", methods=["GET", "POST"])
def staff_login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        cur = mysql.connection.cursor()

        cur.execute("""
        SELECT * FROM staff
        WHERE email = %s
        """, (email,))

        staff_user = cur.fetchone()
        cur.close()

        # check login
        if staff_user and staff_user["password"] == password:

            session["staff_id"] = staff_user["staff_id"]
            session["staff_name"] = staff_user["staff_name"]

            return redirect(url_for("staff.dashboard"))

        else:
            return "Invalid email or password"

    return render_template("staff_login.html")


@staff.route("/staff/register", methods=["GET","POST"])
def staff_register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        password = request.form["password"]
        designation = request.form.get("designation","")

        cur = mysql.connection.cursor()

        cur.execute("""
        INSERT INTO staff (staff_name,email,phone,password,designation)
        VALUES (%s,%s,%s,%s,%s)
        """,(name,email,phone,password,designation))

        mysql.connection.commit()
        cur.close()

        return redirect(url_for("staff.staff_login"))

    return render_template("staff_register.html")

@staff.route("/staff/dashboard")
def dashboard():

    cur = mysql.connection.cursor()

    # =========================
    # TOTAL ORDERS
    # =========================
    cur.execute("""
        SELECT COUNT(*) AS total
        FROM orders
    """)
    total_orders = cur.fetchone()["total"]


    # =========================
    # PLACED ORDERS
    # =========================
    cur.execute("""
        SELECT COUNT(*) AS placed
        FROM orders
        WHERE status = 'Placed'
    """)
    placed_orders = cur.fetchone()["placed"]


    # =========================
    # PENDING ORDERS
    # =========================
    cur.execute("""
        SELECT COUNT(*) AS pending
        FROM orders
        WHERE status = 'Pending'
    """)
    pending_orders = cur.fetchone()["pending"]


    # =========================
    # SHIPPED ORDERS
    # =========================
    cur.execute("""
        SELECT COUNT(*) AS shipped
        FROM orders
        WHERE status = 'Shipped'
    """)
    shipped_orders = cur.fetchone()["shipped"]


    # =========================
    # DELIVERED ORDERS
    # =========================
    cur.execute("""
        SELECT COUNT(*) AS delivered
        FROM orders
        WHERE status = 'Delivered'
    """)
    delivered_orders = cur.fetchone()["delivered"]


    # =========================
    # CANCELLED ORDERS
    # =========================
    cur.execute("""
        SELECT COUNT(*) AS cancelled
        FROM orders
        WHERE status = 'Cancelled'
    """)
    cancelled_orders = cur.fetchone()["cancelled"]


    # =========================
    # TOTAL PRODUCTS
    # =========================
    cur.execute("""
        SELECT COUNT(*) AS total
        FROM products
    """)
    total_products = cur.fetchone()["total"]


    # =========================
    # RECENT ORDERS
    # =========================
    cur.execute("""
        SELECT 
            o.id,
            o.customer_id,
            o.total_amount,
            o.status,
            o.order_date,
            c.customer_name
        FROM orders o
        JOIN customer c
        ON o.customer_id = c.customer_id
        ORDER BY o.order_date DESC
        LIMIT 5
    """)

    recent_orders = cur.fetchall()

    cur.close()

    return render_template(
        "dashboard.html",

        total_orders=total_orders,

        placed_orders=placed_orders,

        pending_orders=pending_orders,

        shipped_orders=shipped_orders,

        delivered_orders=delivered_orders,

        cancelled_orders=cancelled_orders,

        total_products=total_products,

        recent_orders=recent_orders
    )

@staff.route("/staff/products")
def products():

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM products")

    products = cur.fetchall()

    return render_template("staff_products.html", products=products)

from flask import request, render_template, redirect, url_for, send_file
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import io

# =========================
# ORDERS PAGE
# =========================

@staff.route('/staff/orders')
def orders():

    status_filter = request.args.get('status')

    start_date = request.args.get('start_date')

    end_date = request.args.get('end_date')

    cur = mysql.connection.cursor()

    query = """
    SELECT 
        o.id,
        o.total_amount,
        o.status,
        o.order_date,
        c.customer_name,
        c.address,
        p.product_name,
        oi.quantity,
        oi.price

    FROM orders o

    JOIN customer c 
        ON o.customer_id = c.customer_id

    JOIN order_items oi 
        ON o.id = oi.order_id

    JOIN products p 
        ON oi.product_id = p.product_id

    WHERE 1=1
    """

    params = []

    # Status Filter

    if status_filter and status_filter != "All":

        query += " AND o.status = %s"

        params.append(status_filter)

    # Start Date Filter

    if start_date:

        query += " AND DATE(o.order_date) >= %s"

        params.append(start_date)

    # End Date Filter

    if end_date:

        query += " AND DATE(o.order_date) <= %s"

        params.append(end_date)

    query += " ORDER BY o.id DESC"

    cur.execute(query, params)

    data = cur.fetchall()

    # Group Orders

    orders_dict = {}

    for row in data:

        order_id = row['id']

        if order_id not in orders_dict:

            orders_dict[order_id] = {

                "id": row['id'],

                "customer_name": row['customer_name'],

                "address": row['address'],

                "total_amount": row['total_amount'],

                "status": row['status'],

                "order_date": row['order_date'],

                "order_items": []

            }

        orders_dict[order_id]["order_items"].append({

            "name": row['product_name'],

            "qty": row['quantity'],

            "price": row['price']

        })

    orders = list(orders_dict.values())

    return render_template(

        'staff/orders.html',

        orders=orders,

        selected_status=status_filter,

        start_date=start_date,

        end_date=end_date

    )
@staff.route('/staff/update_order_status', methods=['POST'])
def update_order_status():

    order_id = request.form['order_id']
    new_status = request.form['status']

    cur = mysql.connection.cursor()

    # ✅ current status
    cur.execute(
        "SELECT status FROM orders WHERE id=%s",
        (order_id,)
    )

    current_status = cur.fetchone()['status']

    # ❌ prevent editing completed orders
    if current_status in ['Delivered', 'Cancelled']:

        cur.close()

        return redirect(url_for('staff.orders'))

    # ✅ update status
    cur.execute(
        "UPDATE orders SET status=%s WHERE id=%s",
        (new_status, order_id)
    )

    mysql.connection.commit()

    # ✅ customer details
    cur.execute("""

        SELECT
            customer.customer_email,
            orders.order_date

        FROM orders

        JOIN customer
        ON orders.customer_id = customer.customer_id

        WHERE orders.id = %s

    """, (order_id,))

    order_data = cur.fetchone()

    # ✅ ordered products
    cur.execute("""

        SELECT
            products.product_name,
            order_items.quantity,
            order_items.price

        FROM order_items

        JOIN products
        ON order_items.product_id = products.product_id

        WHERE order_items.order_id = %s

    """, (order_id,))

    items = cur.fetchall()

    products = []

    for item in items:

        products.append({

            "name": item['product_name'],
            "qty": item['quantity'],
            "price": item['price']

        })

    # ✅ send email only when delivered
    if new_status == "Delivered":

        send_status_email(

            order_data['customer_email'],
            order_id,
            order_data['order_date'],
            new_status,
            products

        )

    cur.close()

    return redirect(url_for('staff.orders'))
# =========================
# PDF REPORT
# =========================
@staff.route('/staff/orders/report')
def orders_report():

    from flask import request, send_file

    from reportlab.platypus import (
        SimpleDocTemplate,
        Table,
        TableStyle,
        Paragraph,
        Spacer
    )

    from reportlab.lib import colors

    from reportlab.lib.styles import getSampleStyleSheet

    from reportlab.lib.pagesizes import landscape, A3

    import io

    # Filters

    status_filter = request.args.get('status')

    start_date = request.args.get('start_date')

    end_date = request.args.get('end_date')

    cur = mysql.connection.cursor()

    query = """
    SELECT 
        o.id,
        o.total_amount,
        o.status,
        o.order_date,
        c.customer_name,
        c.address,
        p.product_name,
        oi.quantity,
        oi.price

    FROM orders o

    JOIN customer c
        ON o.customer_id = c.customer_id

    JOIN order_items oi
        ON o.id = oi.order_id

    JOIN products p
        ON oi.product_id = p.product_id

    WHERE 1=1
    """

    params = []

    # Status Filter

    if status_filter and status_filter != "All":

        query += " AND o.status = %s"

        params.append(status_filter)

    # Start Date Filter

    if start_date:

        query += " AND DATE(o.order_date) >= %s"

        params.append(start_date)

    # End Date Filter

    if end_date:

        query += " AND DATE(o.order_date) <= %s"

        params.append(end_date)

    query += " ORDER BY o.id DESC"

    cur.execute(query, params)

    data = cur.fetchall()

    # Group Orders

    orders_dict = {}

    for row in data:

        order_id = row['id']

        if order_id not in orders_dict:

            orders_dict[order_id] = {

                "customer": row['customer_name'],

                "address": row['address'],

                "total": row['total_amount'],

                "status": row['status'],

                "date": row['order_date'],

                "items": []

            }

        orders_dict[order_id]["items"].append(
            f"{row['product_name']} (x{row['quantity']})"
        )

    # PDF Buffer

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A3),
        rightMargin=20,
        leftMargin=20,
        topMargin=20,
        bottomMargin=20
    )

    elements = []

    styles = getSampleStyleSheet()

    # Title

    title = Paragraph(
        "<font size='20'><b>ORDERS REPORT</b></font>",
        styles['Title']
    )

    elements.append(title)

    elements.append(Spacer(1, 15))

    # Filter Details

    filter_text = ""

    if status_filter and status_filter != "All":

        filter_text += f"<b>Status:</b> {status_filter} &nbsp;&nbsp;"

    if start_date:

        filter_text += f"<b>From:</b> {start_date} &nbsp;&nbsp;"

    if end_date:

        filter_text += f"<b>To:</b> {end_date}"

    if filter_text:

        elements.append(
            Paragraph(filter_text, styles['Normal'])
        )

        elements.append(Spacer(1, 15))

    # Table Data

    table_data = [[
        "ID",
        "Customer",
        "Address",
        "Items",
        "Total",
        "Date",
        "Status"
    ]]

    for order_id, order in orders_dict.items():

        items_text = ", ".join(order["items"])

        table_data.append([

            Paragraph(str(order_id), styles['BodyText']),

            Paragraph(order["customer"], styles['BodyText']),

            Paragraph(order["address"], styles['BodyText']),

            Paragraph(items_text, styles['BodyText']),

            Paragraph(f"Rs. {order['total']}", styles['BodyText']),

            Paragraph(
                order["date"].strftime('%Y-%m-%d'),
                styles['BodyText']
            ),

            Paragraph(order["status"], styles['BodyText'])

        ])

    # Table

    table = Table(
        table_data,
        colWidths=[45, 110, 170, 330, 70, 80, 80],
        repeatRows=1
    )

    # Table Style

    table.setStyle(TableStyle([

        # Wrap Text

        ('WORDWRAP', (0, 0), (-1, -1), 'CJK'),

        # Header

        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#343a40")),

        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),

        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),

        ('FONTSIZE', (0, 0), (-1, 0), 11),

        # Body

        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),

        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),

        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),

        ('FONTSIZE', (0, 1), (-1, -1), 9),

        # Alignment

        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),

        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

        # Grid

        ('GRID', (0, 0), (-1, -1), 1, colors.grey),

        # Padding

        ('TOPPADDING', (0, 0), (-1, -1), 8),

        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),

        ('LEFTPADDING', (0, 0), (-1, -1), 6),

        ('RIGHTPADDING', (0, 0), (-1, -1), 6),

        # Alternate Rows

        ('ROWBACKGROUNDS',
         (0, 1),
         (-1, -1),
         [colors.whitesmoke, colors.beige])

    ]))

    elements.append(table)

    # Build PDF

    doc.build(elements)

    pdf = buffer.getvalue()

    buffer.close()

    return send_file(
        io.BytesIO(pdf),
        as_attachment=True,
        download_name="orders_report.pdf",
        mimetype='application/pdf'
    )
@staff.route("/staff/edit_product/<int:id>", methods=["GET","POST"])
def edit_product(id):

    cur = mysql.connection.cursor()

    if request.method == "POST":

        category = request.form["category"]
        product_name = request.form["product_name"]
        dish_name = request.form["dish_name"]
        description = request.form["description"]
        price = request.form["price"]
        stock = request.form["stock"]

        image = request.files["image"]

        if image.filename != "":
            filename = secure_filename(image.filename)
            image.save(os.path.join("static/uploads", filename))

            cur.execute("""
            UPDATE products
            SET category=%s, product_name=%s, dish_name=%s,
            description=%s, price=%s, stock=%s, image=%s
            WHERE product_id=%s
            """,(category,product_name,dish_name,description,price,stock,filename,id))

        else:

            cur.execute("""
            UPDATE products
            SET category=%s, product_name=%s, dish_name=%s,
            description=%s, price=%s, stock=%s
            WHERE product_id=%s
            """,(category,product_name,dish_name,description,price,stock,id))

        mysql.connection.commit()

        return redirect(url_for("staff.products"))

    cur.execute("SELECT * FROM products WHERE product_id=%s",(id,))
    product = cur.fetchone()

    return render_template("staff/staff_edit_product.html",product=product)
import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = "static/uploads"

@staff.route("/staff/add_product", methods=["GET","POST"])
def add_product():

    if request.method == "POST":

        category = request.form["category"]
        product_name = request.form["product_name"]
        dish_name = request.form["dish_name"]
        description = request.form["description"]
        price = request.form["price"]
        stock = request.form["stock"]

        image = request.files["image"]

        filename = secure_filename(image.filename)
        image.save(os.path.join(UPLOAD_FOLDER, filename))

        cur = mysql.connection.cursor()

        cur.execute("""
        INSERT INTO products
        (category, product_name, dish_name, description, price, stock, image)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        """,(category, product_name, dish_name, description, price, stock, filename))

        mysql.connection.commit()
        cur.close()

        return redirect(url_for("staff.products"))

    return render_template("staff/add_product.html")


@staff.route("/staff/delete_product/<int:id>")
def delete_product(id):

    cur = mysql.connection.cursor()

    cur.execute("DELETE FROM products WHERE product_id=%s",(id,))

    mysql.connection.commit()

    return redirect(url_for("staff.products"))

@staff.route("/suppliers")
def suppliers():

    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT suppliers.supplier_id, suppliers.supplier_name,
               products.product_name, suppliers.phone,
               suppliers.email, suppliers.address
        FROM suppliers
        LEFT JOIN products ON suppliers.product_id = products.product_id
    """)

    suppliers = cursor.fetchall()

    return render_template("staff/suppliers.html", suppliers=suppliers)

@staff.route("/add_supplier", methods=["GET","POST"])
def add_supplier():

    cursor = mysql.connection.cursor()

    cursor.execute("SELECT product_id, product_name FROM products")
    products = cursor.fetchall()

    if request.method == "POST":

        name = request.form["supplier_name"]
        product_id = request.form["product_id"]
        phone = request.form["phone"]
        email = request.form["email"]
        address = request.form["address"]

        cursor.execute("""
            INSERT INTO suppliers
            (supplier_name, product_id, phone, email, address)
            VALUES (%s,%s,%s,%s,%s)
        """,(name, product_id, phone, email, address))

        mysql.connection.commit()

        return redirect(url_for("staff.suppliers"))

    return render_template("add_supplier.html", products=products)

@staff.route("/customers")
def customers():

    cursor = mysql.connection.cursor()

    cursor.execute("""

        SELECT 
            c.customer_id,
            c.customer_name,
            c.customer_email,
            c.phone,
            c.address,
            c.city,

            -- total orders
            COALESCE(o.total_orders, 0) AS total_orders,

            -- latest reward balance
            COALESCE(r.balance, 0) AS reward_points

        FROM customer c

        LEFT JOIN (
            SELECT 
                customer_id,
                COUNT(*) AS total_orders
            FROM orders
            GROUP BY customer_id
        ) o
        ON c.customer_id = o.customer_id

        LEFT JOIN (
            SELECT 
                cr1.customer_id,
                cr1.balance
            FROM customer_rewards cr1
            WHERE cr1.id = (
                SELECT MAX(cr2.id)
                FROM customer_rewards cr2
                WHERE cr1.customer_id = cr2.customer_id
            )
        ) r
        ON c.customer_id = r.customer_id

        ORDER BY c.customer_id DESC

    """)

    customer = cursor.fetchall()

    cursor.close()

    return render_template(
        "staff_customers.html",
        customer=customer
    )

from flask import make_response
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer
)

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle

from datetime import datetime
import io


@staff.route("/product-report-pdf")
def product_report_pdf():

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT
            product_id,
            category,
            product_name,
            price,
            stock
        FROM products
    """)

    products = cur.fetchall()

    buffer = io.BytesIO()

    pdf = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=30
    )

    elements = []

    styles = getSampleStyleSheet()

    # ---------- Title ----------

    title_style = ParagraphStyle(
        name="TitleStyle",
        parent=styles["Heading1"],
        fontSize=24,
        leading=30,
        alignment=TA_CENTER,
        spaceAfter=8
    )

    subtitle_style = ParagraphStyle(
        name="Subtitle",
        parent=styles["Normal"],
        fontSize=11,
        alignment=TA_CENTER,
        textColor=colors.grey,
        spaceAfter=25
    )

    normal_style = ParagraphStyle(
        name="NormalStyle",
        parent=styles["Normal"],
        fontSize=11,
        leading=18,
        alignment=TA_LEFT
    )

    title = Paragraph("PRODUCT REPORT", title_style)

   

    elements.append(title)
   

    # ---------- Summary ----------

    total_products = len(products)

    total_stock = sum(p["stock"] for p in products)

   
    # ---------- Table ----------

    data = [[
        "ID",
        "Category",
        "Product Name",
        "Price",
        "Quantity"
    ]]

    for p in products:

        data.append([

            str(p["product_id"]),

            p["category"],

            p["product_name"],

            f"Rs. {p['price']}",

            str(p["stock"])

        ])

    table = Table(
        data,
        colWidths=[60, 110, 220, 80, 70]
    )

    table.setStyle(TableStyle([

        # Header
        ("BACKGROUND", (0,0), (-1,0), colors.black),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),

        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,0), 11),

        # Body
        ("FONTNAME", (0,1), (-1,-1), "Helvetica"),
        ("FONTSIZE", (0,1), (-1,-1), 10),

        # Alignment
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),

        # Padding
        ("TOPPADDING", (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),

        # Grid
        ("GRID", (0,0), (-1,-1), 1, colors.black),

        # Alternate row effect
        ("BACKGROUND", (0,1), (-1,-1), colors.whitesmoke),

    ]))

    elements.append(table)

    elements.append(Spacer(1, 30))

    # ---------- Footer ----------

    footer = Paragraph(
        "End of Product Report",
        subtitle_style
    )

    elements.append(footer)

    # ---------- Build PDF ----------

    pdf.build(elements)

    buffer.seek(0)

    response = make_response(buffer.getvalue())

    response.headers["Content-Type"] = "application/pdf"

    response.headers["Content-Disposition"] = (
        "attachment; filename=product_report.pdf"
    )

    return response

@staff.route("/supplier/report/pdf")
def supplier_report_pdf():

    cursor = mysql.connection.cursor()

    cursor.execute("""
        SELECT 
            s.supplier_id,
            s.supplier_name,
            p.product_name,
            s.phone,
            s.email,
            s.address
        FROM suppliers s
        LEFT JOIN products p
            ON s.product_id = p.product_id
    """)

    suppliers = cursor.fetchall()

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
    buffer,
    pagesize=letter,
    rightMargin=30,
    leftMargin=30,
    topMargin=30,
    bottomMargin=30
)

    elements = []

    styles = getSampleStyleSheet()

    title = Paragraph("Supplier Report", styles['Title'])

    elements.append(title)
    elements.append(Spacer(1, 12))

    data = [[
        "ID",
        "Supplier Name",
        "Product",
        "Phone",
        "Email",
        "Address"
    ]]

    for s in suppliers:

        data.append([
            s["supplier_id"],
            s["supplier_name"],
            s["product_name"],
            s["phone"],
            s["email"],
            s["address"]
        ])

    table = Table(data)

    table.setStyle(TableStyle([

        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),

        ('GRID', (0,0), (-1,-1), 1, colors.black),

        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),

        ('BACKGROUND', (0,1), (-1,-1), colors.beige),

        ('BOTTOMPADDING', (0,0), (-1,0), 10),

    ]))

    elements.append(table)

    doc.build(elements)

    pdf = buffer.getvalue()

    buffer.close()

    return Response(
        pdf,
        mimetype='application/pdf',
        headers={
            'Content-Disposition':
            'attachment;filename=supplier_report.pdf'
        }
    )

@staff.route("/customer/report/pdf")
def customer_report_pdf():

    from flask import Response
    from reportlab.platypus import (
        SimpleDocTemplate,
        Table,
        TableStyle,
        Paragraph,
        Spacer
    )

    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.pagesizes import letter

    import io

    cursor = mysql.connection.cursor()

    cursor.execute("""
        SELECT 
            c.customer_id,
            c.customer_name,
            c.customer_email,
            c.phone,
            c.address,

            COALESCE(r.reward_points, 0) AS reward_points,

            COALESCE(o.total_orders, 0) AS total_orders

        FROM customer c

        LEFT JOIN (
            SELECT 
                customer_id,
                MAX(balance) AS reward_points
            FROM customer_rewards
            GROUP BY customer_id
        ) r
            ON c.customer_id = r.customer_id

        LEFT JOIN (
            SELECT 
                customer_id,
                COUNT(*) AS total_orders
            FROM orders
            GROUP BY customer_id
        ) o
            ON c.customer_id = o.customer_id

        ORDER BY c.customer_id DESC
    """)

    customers = cursor.fetchall()

    # =========================
    # PDF BUFFER
    # =========================
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=50,
        leftMargin=50,
        topMargin=40,
        bottomMargin=40
    )

    elements = []

    styles = getSampleStyleSheet()

    # =========================
    # TITLE
    # =========================
    title = Paragraph(
        "Customer Report",
        styles['Title']
    )

    elements.append(title)
    elements.append(Spacer(1, 15))

    # =========================
    # TABLE DATA
    # =========================
    data = [[
        "ID",
        "Customer Name",
        "Email",
        "Phone",
        "Address",
        "Orders",
        "Coins"
    ]]

    for c in customers:

        data.append([

            c["customer_id"],

            c["customer_name"]
            if c["customer_name"] else "-",

            c["customer_email"]
            if c["customer_email"] else "-",

            c["phone"]
            if c["phone"] else "-",

            c["address"]
            if c["address"] else "-",

            c["total_orders"],

            c["reward_points"]

        ])

    # =========================
    # TABLE
    # =========================
    table = Table(
        data,
        colWidths=[30, 75, 120, 70, 120, 40, 40]
    )

    table.setStyle(TableStyle([

        # HEADER
        ('BACKGROUND', (0,0), (-1,0), colors.grey),

        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),

        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),

        ('FONTSIZE', (0,0), (-1,0), 9),

        ('BOTTOMPADDING', (0,0), (-1,0), 10),

        # BODY
        ('BACKGROUND', (0,1), (-1,-1), colors.beige),

        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),

        ('FONTSIZE', (0,1), (-1,-1), 7),

        # GRID
        ('GRID', (0,0), (-1,-1), 1, colors.black),

        # ALIGNMENT
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),

        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),

        # PADDING
        ('TOPPADDING', (0,1), (-1,-1), 6),

        ('BOTTOMPADDING', (0,1), (-1,-1), 6),

        ('LEFTPADDING', (0,0), (-1,-1), 4),

        ('RIGHTPADDING', (0,0), (-1,-1), 4),

    ]))

    elements.append(table)

    # =========================
    # BUILD PDF
    # =========================
    doc.build(elements)

    pdf = buffer.getvalue()

    buffer.close()

    cursor.close()

    # =========================
    # RETURN PDF
    # =========================
    return Response(
        pdf,
        mimetype='application/pdf',
        headers={
            'Content-Disposition':
            'attachment;filename=customer_report.pdf'
        }
    )
@staff.route("/staff/logout")
def staff_logout():
    session.pop("staff_id", None)
    session.pop("staff_name", None)

    return redirect(url_for("staff.staff_login"))