# app.py
from flask import render_template, redirect, request, session, url_for, Flask, jsonify
from flask import send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os
import random
import string
from werkzeug.utils import secure_filename

from models import init_app, db
from models.user import User
from models.vegetable_type import VegetableType
from models.product import Product
from models.order import Order
from models.order_item import OrderItem
from models.delivery_slot import DeliverySlot
from models.review import Review

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'
app.config['SESSION_COOKIE_PATH'] = '/'
app.config['SESSION_KEY_PREFIX'] = 'helloo'
app.config['SESSION_COOKIE_NAME'] = 'Bookstorevsession'
app.secret_key = "Kc5c3zTk'-3<&BdL:P92O{_(:-NkY+K"

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
init_app(app)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role')

        if password != confirm_password:
            error = "Passwords do not match"
        elif User.query.filter_by(email=email).first():
            error = "User already exists"
        else:
            user = User(
                username=username,
                email=email,
                password=password,  # No hashing as per your preference
                role=role,
                created_at=datetime.now()
            )
            db.session.add(user)
            db.session.commit()
            return redirect('/login')

    return render_template('register.html', error=error)


@app.route('/login', methods=['GET', 'POST'])
def login():
    from models.user import User

    error = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email, password=password).first()
        if user:
            session['user_id'] = user.id
            session['role'] = user.role
            session['username'] = user.username
            return redirect('/admin/dashboard' if user.role == 'admin' else '/user/dashboard')
        else:
            error = "Invalid email or password"

    return render_template('login.html', error=error)


@app.route('/user/dashboard')
def user_dashboard():
    if 'user_id' not in session or session.get('role') != 'customer':
        return redirect('/login')
    return render_template('user/dashboard.html')


@app.route('/get_products')
def get_products():
    from models.product import Product
    from models.vegetable_type import VegetableType

    products = Product.query.all()
    result = []

    for p in products:
        veg_type = VegetableType.query.get(p.vegetable_type_id)  # Replace `category_id` with `vegetable_type_id`
        print(p.image_url)
        result.append({
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'price': p.price,
            'stock': p.stock,
            'image_url': p.image_url,
            'category': veg_type.type_name if veg_type else 'Uncategorized'
        })

    return jsonify(result)


# @app.route('/add_product', methods=['POST'])
# def add_product():
#     name = request.form.get('name')
#     description = request.form.get('description')
#     price = request.form.get('price')
#     vegetable_type_id = request.form.get('vegetable_type_id')
#     stock = request.form.get('stock')
#     created_by = request.form.get('created_by')
#     file = request.files.get('image_url')
#
#     image_url = None
#     if file and file.filename != '':
#         filename = secure_filename(file.filename)
#         filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#         file.save(filepath)
#         image_url = filepath
#
#     product = Product(
#         name=name,
#         description=description,
#         price=price,
#         vegetable_type_id=vegetable_type_id,
#         stock=stock,
#         image_url=image_url,
#         created_by=created_by,
#         created_at=datetime.now()
#     )
#     try:
#         db.session.add(product)
#         db.session.commit()
#         db.session.close()
#     except Exception as e:
#         db.session.rollback()
#         return jsonify({"message": "Error adding product", "error": str(e)}), 400
#     return jsonify({"message": "Product added successfully."}), 201


@app.route('/product_details/<int:product_id>')
def product_details(product_id):
    from models.product import Product
    from models.vegetable_type import VegetableType
    from models.review import Review
    from models.user import User

    if 'user_id' not in session:
        return redirect('/login')

    product = Product.query.get_or_404(product_id)
    veg_type = VegetableType.query.get(product.vegetable_type_id)

    # Get all reviews for this product with usernames
    review_data = db.session.query(Review, User.username) \
        .join(User, Review.user_id == User.id) \
        .filter(Review.product_id == product.id).all()

    reviews = [{
        'username': username,
        'rating': review.rating,
        'comment': review.comment
    } for review, username in review_data]

    return render_template(
        'user/product_details.html',
        product=product,
        veg_type=veg_type,
        reviews=reviews,
        is_admin=(session.get('role') == 'admin')
    )


@app.route('/add_order', methods=['POST'])
def add_order():
    from models.order import Order
    from datetime import datetime

    if 'user_id' not in session or session.get('role') != 'customer':
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    total_amount = float(data.get('total_amount'))

    order = Order(
        user_id=session['user_id'],
        order_date=datetime.now(),
        total_amount=total_amount,
        status='Pending'
    )
    db.session.add(order)
    db.session.commit()

    return jsonify({'order_id': order.id})


@app.route('/add_order_items', methods=['POST'])
def add_order_items():
    from models.order_item import OrderItem
    from models.product import Product

    data = request.get_json()
    order_id = data['order_id']
    items = data['items']

    for item in items:
        product = Product.query.get(item['product_id'])

        if product and product.stock >= item['quantity']:
            db.session.add(OrderItem(
                order_id=order_id,
                product_id=item['product_id'],
                quantity=item['quantity'],
                price=product.price
            ))
            product.stock -= item["quantity"]
        else:
            return jsonify({'error': f"Not enough stock for product ID {item['product_id']}"}), 400

    db.session.commit()
    return jsonify({'success': True})


@app.route('/cart')
def cart():
    if 'user_id' not in session or session.get('role') != 'customer':
        return redirect('/login')
    return render_template('user/cart.html')


@app.route('/orders')
def orders():
    if 'user_id' not in session or session.get('role') != 'customer':
        return redirect('/login')
    return render_template('user/orders.html')


# @app.route('/get_orders')
# def get_orders():
#     from models.order import Order
#
#     if 'user_id' not in session:
#         return jsonify([])
#
#     orders = Order.query.filter_by(user_id=session['user_id']).order_by(Order.order_date.desc()).all()
#     return jsonify([{
#         'id': o.id,
#         'status': o.status,
#         'order_date': o.order_date.strftime('%Y-%m-%d %H:%M'),
#         'total_amount': o.total_amount
#     } for o in orders])


@app.route('/get_order_details/<int:order_id>')
def get_order_details(order_id):
    from models.order import Order
    from models.order_item import OrderItem
    from models.product import Product

    if 'user_id' not in session:
        return redirect('/login')

    order = Order.query.get_or_404(order_id)

    # Customer can only view their own orders
    if session['role'] == 'customer' and order.user_id != session['user_id']:
        return "Unauthorized", 403

    order_items = OrderItem.query.filter_by(order_id=order.id).all()
    items = []

    for item in order_items:
        product = Product.query.get(item.product_id)
        if product:
            items.append({
                'product_id': item.product_id,
                'name': product.name,
                'image_url': product.image_url,
                'quantity': item.quantity,
                'price': item.price
            })
        else:
            # Product no longer exists, still show basic info from order item
            items.append({
                'product_id': item.product_id,
                'name': "Deleted Product",
                'image_url': "static/images/deleted.png",  # fallback image (optional)
                'quantity': item.quantity,
                'price': item.price
            })

    return render_template('user/order_details.html', order=order, items=items)


@app.route('/submit_review', methods=['POST'])
def submit_review():
    from models.review import Review

    if 'user_id' not in session or session.get('role') != 'customer':
        return redirect('/login')

    user_id = session['user_id']
    product_id = request.form.get('product_id')
    rating = int(request.form.get('rating'))
    comment = request.form.get('comment')
    order_id = request.form.get('order_id')

    review = Review(
        user_id=user_id,
        product_id=product_id,
        rating=rating,
        comment=comment
    )
    db.session.add(review)
    db.session.commit()

    return redirect(f'/get_order_details/{order_id}')


@app.route('/cancel_order', methods=['POST'])
def cancel_order():
    from models.order import Order
    from models.order_item import OrderItem
    from models.product import Product

    if 'user_id' not in session or session.get('role') != 'customer':
        return redirect('/login')

    order_id = request.form.get('order_id')
    order = Order.query.filter_by(id=order_id, user_id=session['user_id']).first()

    if order and order.status.strip().lower() == 'pending':
        order.status = 'Cancelled'

        # Restore stock
        items = OrderItem.query.filter_by(order_id=order.id).all()
        for item in items:
            product = Product.query.get(item.product_id)
            if product:
                product.stock += item.quantity

        db.session.commit()

    return redirect(f'/get_order_details/{order_id}')


@app.route('/admin/top_selling_vegetables')
def top_selling_vegetables():
    from models.product import Product
    from models.order_item import OrderItem

    data = db.session.query(
        Product.id,
        Product.name,
        db.func.sum(OrderItem.quantity).label("total_sold")
    ).join(OrderItem, Product.id == OrderItem.product_id) \
        .group_by(Product.id) \
        .order_by(db.desc("total_sold")) \
        .limit(5).all()

    return jsonify([{'name': name, 'total_sold': int(total_sold)} for _, name, total_sold in data])


@app.route('/get_orders')
def get_orders():
    from models.order import Order

    if 'user_id' not in session:
        return jsonify([])

    if session.get('role') == 'admin':
        orders = Order.query.order_by(Order.order_date.desc()).all()
    else:
        orders = Order.query.filter_by(user_id=session['user_id']).order_by(Order.order_date.desc()).all()

    return jsonify([{
        'id': o.id,
        'status': o.status,
        'order_date': o.order_date.strftime('%Y-%m-%d %H:%M'),
        'total_amount': o.total_amount
    } for o in orders])



@app.route('/get_users')
def get_users():
    from models.user import User

    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify([])

    users = User.query.all()
    return jsonify([{
        'id': u.id,
        'username': u.username,
        'role': u.role
    } for u in users])


@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect('/login')
    return render_template('admin/dashboard.html')


@app.route('/admin/products')
def admin_products():
    from models.product import Product
    from models.vegetable_type import VegetableType  # or use FoodCategory if renamed

    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect('/login')

    products = Product.query.all()
    product_list = []

    for p in products:
        veg_type = VegetableType.query.get(p.vegetable_type_id)
        product_list.append({
            'id': p.id,
            'name': p.name,
            'price': p.price,
            'stock': p.stock,
            'image_url': p.image_url,
            'category': veg_type.type_name if veg_type else "Uncategorized"
        })

    return render_template('admin/products.html', products=product_list)


@app.route('/admin/add_product', methods=['GET', 'POST'])
def add_product():
    from models.product import Product
    from models.vegetable_type import VegetableType

    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect('/login')

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = float(request.form.get('price'))
        stock = int(request.form.get('stock'))
        vegetable_type_id = int(request.form.get('vegetable_type_id'))

        # Handle image upload
        image_file = request.files.get('image')
        image_url = ''
        if image_file and image_file.filename:
            filename = secure_filename(image_file.filename)
            image_path = os.path.join('uploads', filename)
            image_file.save(image_path)
            image_url = image_path  # relative path used in frontend

        product = Product(
            name=name,
            description=description,
            price=price,
            stock=stock,
            vegetable_type_id=vegetable_type_id,
            image_url=image_url,
            created_by=session['user_id'],
            created_at=datetime.now()
        )

        try:
            db.session.add(product)
            db.session.commit()
            return redirect('/admin/products')
        except Exception as e:
            db.session.rollback()
            return f"Error adding product: {str(e)}", 500

    # GET request
    categories = VegetableType.query.order_by(VegetableType.type_name.asc()).all()
    return render_template('admin/add_product.html', categories=categories)


@app.route('/admin/delete_product', methods=['POST'])
def delete_product():
    from models.product import Product

    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect('/login')

    product_id = request.form.get('product_id')
    product = Product.query.get(product_id)

    if product:
        db.session.delete(product)
        db.session.commit()

    return redirect('/admin/products')


@app.route('/update_stock', methods=['POST'])
def update_stock():
    from models.product import Product

    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect('/login')

    product_id = request.form.get('product_id')
    new_stock = int(request.form.get('stock'))

    product = Product.query.get(product_id)
    if product:
        product.stock = new_stock
        db.session.commit()

    return redirect(f'/product_details/{product_id}')



@app.route('/admin/users')
def admin_users():
    from models.user import User

    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect('/login')

    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)


@app.route('/admin/delete_user', methods=['POST'])
def admin_delete_user():
    from models.user import User

    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect('/login')

    user_id = request.form.get('user_id')
    user = User.query.get(user_id)

    if user:
        db.session.delete(user)
        db.session.commit()

    return redirect('/admin/users')


@app.route('/admin/orders')
def admin_orders():
    from models.order import Order

    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect('/login')

    orders = Order.query.order_by(Order.order_date.desc()).all()
    return render_template('admin/orders.html', orders=orders)


@app.route('/admin/cancel_order', methods=['POST'])
def admin_cancel_order():
    from models.order import Order
    from models.order_item import OrderItem
    from models.product import Product

    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect('/login')

    order_id = request.form.get('order_id')
    order = Order.query.get(order_id)

    if order and order.status.strip().lower() == 'pending':
        order.status = 'Cancelled'

        # Restore stock
        items = OrderItem.query.filter_by(order_id=order.id).all()
        for item in items:
            product = Product.query.get(item.product_id)
            if product:
                product.stock += item.quantity

        db.session.commit()

    return redirect('/admin/orders')


@app.route('/admin/mark_delivered', methods=['POST'])
def admin_mark_delivered():
    from models.order import Order

    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect('/login')

    order_id = request.form.get('order_id')
    order = Order.query.get(order_id)

    if order and order.status.strip().lower() == 'pending':
        order.status = 'Delivered'
        db.session.commit()

    return redirect('/admin/orders')


@app.route('/admin/vegetable_types', methods=['GET', 'POST'])
def admin_vegetable_types():
    from models.vegetable_type import VegetableType

    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect('/login')

    error_message = None

    if request.method == 'POST':
        type_name = request.form.get('type_name')
        description = request.form.get('description', '')

        # Prevent duplicates
        existing = VegetableType.query.filter_by(type_name=type_name).first()
        if existing:
            error_message = f"Type '{type_name}' already exists."
        else:
            new_type = VegetableType(type_name=type_name.strip(), description=description.strip())
            db.session.add(new_type)
            db.session.commit()
            return redirect('/admin/vegetable_types')

    types = VegetableType.query.order_by(VegetableType.id.desc()).all()
    return render_template('admin/vegetable_types.html', vegetable_types=types, error_message=error_message)


@app.route('/admin/delete_vegetable_type', methods=['POST'])
def delete_vegetable_type():
    from models.vegetable_type import VegetableType

    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect('/login')

    veg_type_id = request.form.get('vegetable_type_id')
    veg_type = VegetableType.query.get(veg_type_id)

    if veg_type:
        db.session.delete(veg_type)
        db.session.commit()

    return redirect('/admin/vegetable_types')




if __name__ == '__main__':
    app.run(debug=True)
