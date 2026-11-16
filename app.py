from flask import Flask, render_template
from pathlib import Path
from models import get_db, init_app, init_db

app = Flask(__name__)


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contacts')
def contacts():
    return render_template('contacts.html')


@app.route('/shop')
def shop():
    return render_template('shop.html')


Path(app.instance_path).mkdir(parents=True, exist_ok=True)
app.config["DATABASE"] = str(
    Path(app.instance_path) / "loq_market.sqlite3")

init_app(app)

# Створює файл БД, якщо його ще немає
with app.app_context():
    get_db()
    init_db()

if __name__ == '__main__':
    # debug=True: автоматичний перезапуск після змін у коді та детальні повідомлення про помилки.
    # Використовується лише під час розробки.
    app.run(debug=True, use_reloader=False)
