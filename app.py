from pathlib import Path

from flask import Flask, abort, flash, redirect, render_template, request, url_for

from models import (
    ORDER_STATUSES, STATUS_LABELS, create_feedback, create_order, delete_feedback,
    delete_product, get_all_feedback, get_db, get_orders, get_product,
    get_products, init_app, init_db, save_product, update_order_status,
)

app = Flask(__name__)
app.config["SECRET_KEY"] = "loq-market-development-key"
Path(app.instance_path).mkdir(parents=True, exist_ok=True)
app.config["DATABASE"] = str(Path(app.instance_path) / "loq_market.sqlite3")
init_app(app)


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contacts", methods=["GET", "POST"])
def contacts():
    if request.method == "POST":
        name, email, message = (request.form.get(key, "").strip() for key in ("name", "email", "message"))
        if not name or not email or "@" not in email or not message:
            flash("Заповни всі поля та вкажи коректну електронну адресу.", "error")
        else:
            create_feedback(name, email, message)
            flash("Дякуємо! Твій відгук збережено.", "success")
        return redirect(url_for("contacts"))
    return render_template("contacts.html")


@app.route("/admin")
def admin():
    return redirect(url_for("admin_products"))


@app.route("/admin/feedback")
def admin_feedback():
    return render_template("admin_feedback.html", feedback_entries=get_all_feedback())


@app.post("/admin/feedback/<int:feedback_id>/delete")
def admin_delete_feedback(feedback_id):
    flash("Відгук видалено." if delete_feedback(feedback_id) else "Відгук уже не існує.", "success")
    return redirect(url_for("admin_feedback"))


@app.route("/admin/products")
def admin_products():
    return render_template("admin_products.html", products=get_products())


def product_form_values():
    weapon = request.form.get("weapon", "").strip()
    skin = request.form.get("skin", "").strip()
    quality = request.form.get("quality", "").strip()
    image_url = request.form.get("image_url", "").strip()
    try:
        price = float(request.form.get("price", ""))
        stock = int(request.form.get("stock", ""))
    except ValueError:
        raise ValueError("Ціна має бути числом, а залишок — цілим числом.")
    if not weapon or not skin or not quality or price < 0 or stock < 0:
        raise ValueError("Заповни назву, стан, ціну та залишок коректно.")
    return weapon, skin, quality, price, image_url, stock


@app.post("/admin/products/save")
def admin_save_product():
    product_id = request.form.get("product_id", "").strip()
    try:
        product_id = int(product_id) if product_id else None
        save_product(product_id, *product_form_values())
        flash("Товар збережено.", "success")
    except ValueError as error:
        flash(str(error), "error")
    return redirect(url_for("admin_products"))


@app.post("/admin/products/<int:product_id>/delete")
def admin_delete_product(product_id):
    if delete_product(product_id):
        flash("Товар видалено.", "success")
    else:
        flash("Товар не знайдено або він уже входить до замовлення.", "error")
    return redirect(url_for("admin_products"))


@app.route("/admin/orders")
def admin_orders():
    return render_template("admin_orders.html", orders=get_orders(), statuses=ORDER_STATUSES, status_labels=STATUS_LABELS)


@app.post("/admin/orders/<int:order_id>/status")
def admin_order_status(order_id):
    try:
        updated = update_order_status(order_id, request.form.get("status", ""))
        flash("Статус замовлення оновлено." if updated else "Замовлення не знайдено.", "success" if updated else "error")
    except ValueError as error:
        flash(str(error), "error")
    return redirect(url_for("admin_orders"))


@app.route("/shop")
def shop():
    return render_template("shop.html", products=get_products())


@app.route("/shop/<int:product_id>/order", methods=["GET", "POST"])
def order_product(product_id):
    product = get_product(product_id)
    if product is None:
        abort(404)
    if request.method == "POST":
        customer_name = request.form.get("customer_name", "").strip()
        customer_email = request.form.get("customer_email", "").strip()
        try:
            quantity = int(request.form.get("quantity", ""))
        except ValueError:
            quantity = 0
        if not customer_name or not customer_email or "@" not in customer_email:
            flash("Вкажи ім’я та коректну електронну адресу.", "error")
            return redirect(url_for("order_product", product_id=product_id))
        try:
            order_id = create_order(product_id, customer_name, customer_email, quantity)
        except ValueError as error:
            flash(str(error), "error")
            return redirect(url_for("order_product", product_id=product_id))
        flash(f"Замовлення №{order_id} оформлено.", "success")
        return redirect(url_for("shop"))
    return render_template("order.html", product=product)


with app.app_context():
    init_db()


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
