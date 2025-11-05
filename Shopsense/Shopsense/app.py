
from flask import Flask, render_template, request, redirect, session, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash


import os

# -----------------------------
# ⚙️ CONFIGURATION
# -----------------------------
app = Flask(__name__,
            static_folder='.',        # CSS, JS, Images are in same folder
            static_url_path='',
            template_folder='.')      # HTML files also in same folder

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clothkart.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "clothkart_secret_key"

db = SQLAlchemy(app)

# -----------------------------
# 🧱 DATABASE MODELS
# -----------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    image = db.Column(db.String(200))

class Subscriber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100))
    price = db.Column(db.Float)
    quantity = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(200))
    message = db.Column(db.Text, nullable=False)

# -----------------------------
# 🏠 FRONTEND ROUTES
# -----------------------------
@app.route('/')
def home():
    return render_template('index.html')


# @app.route('/shop')
# def shop():
#     products = Product.query.all()
#     return render_template('shop.html', products=products)


@app.route('/about')
def about():
    return render_template('about.html')


# @app.route('/contact')
# def contact():
#     return render_template('contact.html')


@app.route('/account')
def account():
    user = None
    if "user_id" in session:
        user = User.query.get(session["user_id"])
    return render_template('account.html', user=user)


@app.route('/sproduct')
def sproduct():
    return render_template('sproduct.html')


# -----------------------------
# 👤 REGISTER & LOGIN
# -----------------------------
@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")

    if not username or not email or not password:
        flash("⚠️ Please fill all fields!", "error")
        return redirect("/account")

    existing_user = User.query.filter((User.email == email) | (User.username == username)).first()
    if existing_user:
        flash("❌ Username or Email already exists!", "error")
        return redirect("/account")

    hashed_pw = generate_password_hash(password)
    new_user = User(username=username, email=email, password=hashed_pw)
    db.session.add(new_user)
    db.session.commit()

    flash("✅ Registration successful! Please login now.", "success")
    return redirect("/account")


@app.route("/login", methods=["POST"])
def login():
    email = request.form.get("email")
    password = request.form.get("password")

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password, password):
        flash("❌ Invalid email or password!", "error")
        return redirect("/account")

    session["user_id"] = user.id
    flash(f"👋 Welcome back, {user.username}!", "success")
    return redirect("/account")


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("👋 Logged out successfully!", "info")
    return redirect("/account")



# -----------------------------
# 🛒 CART SYSTEM
# -----------------------------
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'user_id' not in session:
        flash("Please login first!", "warning")
        return redirect(url_for('account'))

    product_name = request.form.get('product_name')
    price = float(request.form.get('price'))
    quantity = int(request.form.get('quantity', 1))

    new_item = Cart(product_name=product_name, price=price, quantity=quantity, user_id=session['user_id'])
    db.session.add(new_item)
    db.session.commit()

    flash("🛍️ Item added to cart!", "success")
    return redirect(url_for('view_cart'))


# @app.route('/cart')
# def view_cart():
#     if 'user_id' not in session:
#         flash("Please login first!", "warning")
#         return redirect(url_for('account'))

#     cart_items = Cart.query.filter_by(user_id=session['user_id']).all()
#     total = sum(item.price * item.quantity for item in cart_items)
#     return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/cart')
def view_cart():
    if 'user_id' not in session:
        return redirect('/account')

    cart_items = Cart.query.filter_by(user_id=session['user_id']).all()
    total = sum(item.price * item.quantity for item in cart_items)

    html = """
    <html>
    <head>
        <title>🛒 My Cart - ClothKart</title>
        <style>
            body {font-family: Arial; background: #f8f9fa; padding: 30px;}
            table {width: 100%; border-collapse: collapse; background: white;}
            th, td {padding: 12px; border-bottom: 1px solid #ccc;}
            th {background: #1d4ed8; color: white;}
            tr:hover {background: #eef2ff;}
            .total {text-align: right; margin-top: 20px; font-size: 18px;}
            .btn {background: #2563eb; color: white; padding: 10px 18px; text-decoration: none; border-radius: 5px;}
            .btn:hover {background: #1e40af;}
        </style>
    </head>
    <body>
        <h2>🛒 Your Shopping Cart</h2>
        <table>
            <tr><th>Product</th><th>Price (₹)</th><th>Quantity</th><th>Subtotal</th><th>Action</th></tr>
    """
    for item in cart_items:
        subtotal = item.price * item.quantity
        html += f"""
        <tr>
            <td>{item.product_name}</td>
            <td>{item.price}</td>
            <td>{item.quantity}</td>
            <td>{subtotal}</td>
            <td><a href='/remove_from_cart/{item.id}' class='btn'>Remove</a></td>
        </tr>
        """
    html += f"""
        </table>
        <div class="total"><strong>Total: ₹{total}</strong></div>
        <br><a href='/shop' class='btn'>🛍 Continue Shopping</a>
    </body></html>
    """
    return html


@app.route('/remove_from_cart/<int:item_id>')
def remove_from_cart(item_id):
    if 'user_id' not in session:
        flash("Please login first!", "warning")
        return redirect(url_for('account'))

    item = Cart.query.get(item_id)
    if item:
        db.session.delete(item)
        db.session.commit()
        flash("🗑️ Item removed from cart.", "info")

    return redirect(url_for('view_cart'))


# -----------------------------
# 🧩 INIT DATABASE (CREATE + SAMPLE DATA)
# -----------------------------
@app.route("/initdb")
def initdb():
    db.drop_all()
    db.create_all()

    sample_products = [
        Product(name="Red Dress", price=799, description="Stylish red dress", image="img/product1.jpg"),
        Product(name="Blue Jeans", price=1199, description="Comfortable blue jeans", image="img/product2.jpg"),
        Product(name="White Shirt", price=699, description="Cotton casual shirt", image="img/product3.jpg"),
    ]
    db.session.add_all(sample_products)
    db.session.commit()
    return "✅ Database initialized with sample products!"


# -----------------------------
# 🔍 SHOW DATABASE DATA
# -----------------------------


@app.route("/showdata")
def showdata():
    users = User.query.all()
    products = Product.query.all()
    carts = Cart.query.all()
    contacts = Contact.query.all()
    subscribers = Subscriber.query.all()

    html = """
    <html>
    <head>
        <title>📊 ClothKart | Admin Dashboard</title>
        <style>
            * {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            body {
                margin: 0;
                background-color: #e8f1ff; /* 🌤️ light professional blue */
                padding: 30px;
                color: #333;
            }
            h1 {
                text-align: center;
                color: #1e3a8a;
                margin-bottom: 30px;
                font-size: 2.5rem;
                letter-spacing: 1px;
                text-shadow: 1px 1px 2px #b3c8ff;
            }
            h2 {
                margin-top: 40px;
                color: #334155;
            }
            .table-container {
                background: white;
                border-radius: 15px;
                padding: 20px;
                margin-bottom: 40px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.08);
                transition: transform 0.2s ease-in-out;
            }
            .table-container:hover {
                transform: translateY(-3px);
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 15px;
            }
            th, td {
                border: 1px solid #e5e5e5;
                padding: 10px 14px;
                text-align: left;
            }
            th {
                background: #1d4ed8;
                color: white;
                text-transform: uppercase;
                font-size: 14px;
                letter-spacing: 0.5px;
            }
            tr:nth-child(even) {
                background-color: #f8faff;
            }
            tr:hover {
                background-color: #eef4ff;
            }
            td {
                font-size: 15px;
            }
            footer {
                text-align: center;
                color: #555;
                margin-top: 50px;
                font-size: 14px;
            }
            .badge {
                background: #2563eb;
                color: white;
                padding: 3px 8px;
                border-radius: 6px;
                font-size: 13px;
            }
            .back-btn {
                display: inline-block;
                padding: 10px 20px;
                background-color: #1d4ed8;
                color: white;
                text-decoration: none;
                border-radius: 8px;
                transition: background 0.2s ease-in-out;
                font-weight: 500;
            }
            .back-btn:hover {
                background-color: #1e40af;
            }
            .btn-container {
                text-align: center;
                margin-bottom: 30px;
            }
        </style>
    </head>
    <body>
        <div class="btn-container">
            <a href="/" class="back-btn">🏠 Back to Home</a>
        </div>

        <h1>🧾 ClothKart Database Dashboard</h1>

        <div class="table-container">
            <h2>👤 Users <span class="badge">{len(users)}</span></h2>
            <table>
                <tr><th>ID</th><th>Username</th><th>Email</th></tr>
    """

 
    # USERS
    for u in users:
        html += f"<tr><td>{u.id}</td><td>{u.username}</td><td>{u.email}</td></tr>"
    html += "</table></div>"

    # PRODUCTS
    html += f"""
        <div class="table-container">
            <h2>🛍️ Products <span class="badge">{len(products)}</span></h2>
            <table>
                <tr><th>ID</th><th>Name</th><th>Price (₹)</th><th>Description</th></tr>
    """
    for p in products:
        html += f"<tr><td>{p.id}</td><td>{p.name}</td><td>{p.price}</td><td>{p.description}</td></tr>"
    html += "</table></div>"

    # CART ITEMS
      # CART ITEMS (Enhanced View)
    # html += f"""
    #      <div class="table-container">
    #     <h2>🛒 Cart Items <span class="badge">{len(carts)}</span></h2>
    #     <table>
    #         <tr>
    #             <th>ID</th>
    #             <th>User</th>
    #             <th>Product</th>
    #             <th>Price (₹)</th>
    #             <th>Quantity</th>
    #             <th>Subtotal (₹)</th>
    #         </tr>
    # """
    # for c in carts:
    #    user = User.query.get(c.user_id)
    # username = user.username if user else "Guest"
    # subtotal = c.price * c.quantity
    # html += f"<tr><td>{c.id}</td><td>{username}</td><td>{c.product_name}</td><td>{c.price}</td><td>{c.quantity}</td><td>{subtotal}</td></tr>"
    # html += "</table></div>"
    
     # CART ITEMS (Enhanced View)
    html += f"""
    <div class="table-container">
        <h2>🛒 Cart Items <span class="badge">{len(carts)}</span></h2>
        <table>
            <tr>
                <th>ID</th>
                <th>User</th>
                <th>Product</th>
                <th>Price (₹)</th>
                <th>Quantity</th>
                <th>Subtotal (₹)</th>
            </tr>
    """

    for c in carts:
      user = User.query.get(c.user_id)
      username = user.username if user else "Guest"
      subtotal = c.price * c.quantity
      html += f"<tr><td>{c.id}</td><td>{username}</td><td>{c.product_name}</td><td>{c.price}</td><td>{c.quantity}</td><td>{subtotal}</td></tr>"

    html += "</table></div>"


    # CONTACT MESSAGES
    html += f"""
        <div class="table-container">
            <h2>📨 Contact Messages <span class="badge">{len(contacts)}</span></h2>
            <table>
                <tr><th>ID</th><th>Name</th><th>Email</th><th>Subject</th><th>Message</th></tr>
    """
    for msg in contacts:
        html += f"<tr><td>{msg.id}</td><td>{msg.name}</td><td>{msg.email}</td><td>{msg.subject}</td><td>{msg.message}</td></tr>"
    html += "</table></div>"

    # SUBSCRIBERS
    html += f"""
        <div class="table-container">
            <h2>📧 Subscribers <span class="badge">{len(subscribers)}</span></h2>
            <table>
                <tr><th>ID</th><th>Email</th></tr>
    """
    for s in subscribers:
        html += f"<tr><td>{s.id}</td><td>{s.email}</td></tr>"
    html += "</table></div>"

    html += """
        <footer>© 2025 ClothKart | Admin Panel Interface</footer>
    </body>
    </html>
    """

    return html







@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')

        if not name or not email or not message:
            flash("⚠️ Please fill in all required fields!", "error")
            return redirect(url_for('contact'))

        new_contact = Contact(name=name, email=email, subject=subject, message=message)
        db.session.add(new_contact)
        db.session.commit()

        flash("✅ Your message has been sent successfully!", "success")
        return redirect(url_for('contact'))

    return render_template('contact.html')









# ------------------------------
# Route for newsletter form
# ------------------------------
@app.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.form.get('email')

    if not email:
        flash('Please enter a valid email address!', 'error')
        return redirect(request.referrer)

    # Check if already subscribed
    existing = Subscriber.query.filter_by(email=email).first()
    if existing:
        flash('You are already subscribed!', 'info')
        return redirect(request.referrer)

    # Save new subscriber
    new_subscriber = Subscriber(email=email)
    db.session.add(new_subscriber)
    db.session.commit()

    flash('Subscribed successfully! 🎉', 'success')
    return redirect(request.referrer)
@app.route('/shop')
def shop():
    products = [
        {"name": "Cartoon Floral Art T-Shirt", "price": 49, "image": "img/products/f1.jpg", "description": "Cool summer shirt"},
        {"name": "Blue Denim Shirt", "price": 79, "image": "img/products/f2.jpg", "description": "Stylish denim"},
        {"name": "Casual Hoodie", "price": 99, "image": "img/products/f3.jpg", "description": "Comfy winter hoodie"},
    ]
    return render_template('shop.html', products=products)

# -----------------------------
# 🚀 RUN SERVER
# -----------------------------
if __name__ == "__main__":
    if not os.path.exists("clothkart.db"):
        with app.app_context():
            db.create_all()
    app.run(debug=True)

