import sqlite3
from flask import Flask, request, make_response, render_template, url_for, redirect, session, flash
from flask_session import Session
from werkzeug.exceptions import abort
import os
from werkzeug.utils import secure_filename

from flask_bcrypt import Bcrypt


bcrypt = Bcrypt()
app = Flask(__name__, template_folder="templates")

UPLOAD_FOLDER = '/static/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['SECRET_KEY'] = 'e[rl349534hetdgrig4uwot5a3whef;eqt;wy3yg'
Session(app)

k_auth = 'auth'


def get_db_connection():
    conn = sqlite3.connect('database/database.db')
    conn.row_factory = sqlite3.Row
    return conn


def get_product_id(pid):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE product_id = ?',
                           (pid,)).fetchone()
    conn.close()
    if product is None:
        abort(404)
    return product


def get_productparam_id(pid):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM product_parameters WHERE p_id = ?',
                           (pid,)).fetchone()
    conn.close()
    if product is None:
        abort(404)
    return product


def is_login():
    return session.get('auth')


def get_id():
    conn = get_db_connection()
    login = session['name']
    user = conn.execute('SELECT * FROM users WHERE login = ?', (login,)).fetchone()
    conn.close()
    if login is None:
        abort(404)
    return user['id']


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))





@app.route("/logout", methods=['GET'])
def logout():
    session['name'] = None
    return redirect("/")


@app.route("/")
@app.route("/products", methods=('GET', 'POST'))
def products_list():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    return render_template("main.html", products=products)


@app.route("/products/<int:pid>/delete", methods=('GET', 'POST'))
def product_delete(pid):
    conn = get_db_connection()
    product = get_product_id(pid)
    user_id = get_id()
    if request.method == 'GET':
        return render_template('delete.html', product=product)
    if request.method == 'POST':
        if user_id == product['user_id']:  # сравнение для проверки, что товар принадлежит юзеру
            conn.execute("DELETE FROM products WHERE product_id=?", (product['product_id'],))
            conn.execute('DELETE FROM product_parameters WHERE p_id=?', (product['product_id'],))
            conn.commit()
            conn.close()
            return redirect(url_for('products_list'))


@app.route('/products/<int:pid>/edit', methods=('GET', 'POST'))
def product_edit(pid):
    product = get_product_id(pid)
    product_params = get_productparam_id(pid)
    if request.method == 'POST':
        user_id = get_id()
        name = request.form.get('name')
        price = request.form.get('price')
        description = request.form.get('description')
        lvl = request.form.get('lvl')
        score = request.form.get('score')

        if not name:
            print('kek')
        else:
            if user_id == product['user_id']:  # то же самое, что и выше
                conn = get_db_connection()
                conn.execute('UPDATE products SET name = ?, price = ?, description = ?'
                             ' WHERE product_id = ?',
                             (name, price, description, product['product_id']))
                conn.execute('UPDATE product_parameters SET lvl = ?, score = ? WHERE p_id = ?', (lvl, score, product['product_id']))
                conn.commit()
                conn.close()
                return redirect(url_for('products_list'))

    return render_template('edit.html', product=product, product_params=product_params)


@app.route('/create', methods=('GET', 'POST'))
def product_create():
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        description = request.form['description']
        lvl = request.form['lvl']
        score = request.form['score']
        file = request.form['file']

        if not name:
            print('kek')
        else:
            conn = get_db_connection()
            login = session['name']

            if login:
                user = conn.execute('SELECT * FROM users WHERE login = ?', (login,)).fetchone()
                insert(table_name='products', name=name, price=price, description=description, user_id=user['id'], image=file)
                product_id = conn.execute('SELECT product_id FROM products WHERE user_id = ?', (user['id'],)).fetchall()[-1]['product_id']
                # print(product_id)
                insert(table_name='product_parameters', p_id=product_id, lvl=lvl, score=score)
                conn.commit()
                conn.close()
                return redirect(url_for('products_list'))

    return render_template('create.html')



@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        login = request.form.get('login')
        password = request.form.get('password')

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE login = ?", (login,)).fetchone()

        if user and bcrypt.check_password_hash(user['password'], password):
            session['user_id'] = user['id']  # создаем сессию, чтобы ...
            session['name'] = request.form.get('login')
            return redirect(url_for('products_list'))

    return render_template('login.html')


def insert(table_name, **kwargs):
    conn = get_db_connection()
    arg_q = ', '.join(["?"] * (len(kwargs)))
    arg_names = ",".join(kwargs.keys())

    arg_values = tuple(kwargs.values())
    sql_raw = f"insert into {table_name} ({arg_names}) values ({arg_q})"
    conn.execute(sql_raw, arg_values)
    conn.commit()
    conn.close()


def add_to_cart(user_id, p_id):
    if session['name']:
        insert(table_name='cart', user_id=user_id, pic_id=p_id)
    else:
        render_template('signup.html')


@app.route("/cart/", methods=['GET', 'POST'])
def cart(p_id):
    if session['name']:
        user_id = get_id()
        p_id = get_product_id(p_id)
        add_to_cart(user_id, p_id[0])
        return render_template('cart.html', p_id=p_id)
    else:
        render_template('signup.html')


@app.route("/signup", methods=['GET', 'POST'])
def signup():

    if request.method == "POST":
        login = request.form.get('login')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        phone = request.form.get('phone')
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE login = ?", (login,)).fetchall()
        print(123)

        if not user and password1 == password2:
            pw_hash = bcrypt.generate_password_hash(password1)
            insert(table_name='users', login=login, password=pw_hash, phone=phone)
            id = conn.execute("SELECT id FROM users ORDER BY id DESC LIMIT 1").fetchone()
            insert(table_name='profiles', user_id=id[0], name=login)
            session['name'] = login
            session[k_auth] = True

            return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/profile', methods=('GET', 'POST'))
def profile():
    conn = get_db_connection()
    profile_id = get_id()
    description = conn.execute("SELECT description FROM profiles WHERE user_id = ?", (profile_id,)).fetchone()[0]
    name = conn.execute("SELECT name FROM profiles WHERE user_id = ?", (profile_id,)).fetchone()[0]
    if request.method == 'POST':
        user_id = get_id()
        name = request.form.get('name')
        description = request.form.get('description')
        file = request.form.get('file')
        if user_id == profile_id:
            conn = get_db_connection()
            conn.execute('UPDATE profiles SET name = ?, description = ?'
                         ' WHERE profile_id = ?',
                         (name, description, profile_id))
            conn.commit()
            conn.close()
    return render_template('profile.html', product=profile_id, name=name, description=description)


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000, debug=True)
