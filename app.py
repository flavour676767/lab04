from pathlib import Path

from flask import Flask, abort, flash, redirect, render_template, request, url_for

from models import (
    create_feedback,
    create_order,
    delete_feedback,
    get_all_feedback,
    get_db,
    get_product,
    get_products,
    init_app,
    init_db,
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
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        message = request.form.get("message", "").strip()

        if not name or not email or "@" not in email or not message:
            flash("Заповни всі поля та вкажи коректну електронну адресу.", "error")
        else:
            create_feedback(name, email, message)
            flash("Дякуємо! Твій відгук збережено.", "success")
        return redirect(url_for("contacts"))

    return render_template("contacts.html")


@app.route("/admin/feedback")
def admin_feedback():
    return render_template(
        "admin_feedback.html",
        feedback_entries=get_all_feedback(),
    )


@app.post("/admin/feedback/<int:feedback_id>/delete")
def admin_delete_feedback(feedback_id):
    if delete_feedback(feedback_id):
        flash("Відгук видалено.", "success")
    else:
        flash("Відгук уже не існує.", "error")
    return redirect(url_for("admin_feedback"))


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
            order_id = create_order(
                product_id,
                customer_name,
                customer_email,
                quantity,
            )
        except ValueError as error:
            flash(str(error), "error")
            return redirect(url_for("order_product", product_id=product_id))

        flash(f"Замовлення №{order_id} оформлено.", "success")
        return redirect(url_for("shop"))

    return render_template("order.html", product=product)


with app.app_context():
    get_db()
    init_db()


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
