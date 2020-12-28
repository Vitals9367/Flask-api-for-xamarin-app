from flask import Flask, jsonify, request, make_response, send_file
from flask.globals import session
from flask_restful import Api, Resource, reqparse, abort, fields, marshal_with
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from dataclasses import dataclass
from sqlalchemy import schema
from marshmallow_sqlalchemy import ModelSchema
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
from sqlalchemy.orm import backref
from functools import wraps
from datetime import datetime, timedelta
import os
import urllib.parse
import uuid
import jwt

# --- Config ------------------------------------------------------------------------------------

params = urllib.parse.quote_plus(
    "DRIVER={ODBC Driver 17 for SQL Server};SERVER=xamdb.database.windows.net;DATABASE=XamarinDB;UID=vitalijusal9367;PWD=mariukas1A.")

app = Flask(__name__)
api = Api(app)

app.config['SQLALCHEMY_DATABASE_URI'] = "mssql+pyodbc:///?odbc_connect=%s" % params
app.config['SQLALCHEMY_ECHO'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SECRET_KEY'] = '\xfd{H\xe5<\x95\xf9\xe3\x96.5\xd1\x01O<!\xd5\xa2\xa0\x9fR"\xa1\xa8'

db = SQLAlchemy(app)
ma = Marshmallow(app)

# --- Models ------------------------------------------------------------------------------


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(300), unique=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(300), nullable=False)
    info = db.relationship(
        "User_Info", cascade="all, delete-orphan", uselist=False, backref="user")
    cart = db.relationship(
        "Cart", cascade="all, delete-orphan", uselist=False, backref="user")
    orders = db.relationship("Orders", backref="user")
    reviews = db.relationship("Reviews", backref="user")
    is_admin = db.Column(db.Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"User('{self.username}')"


class User_Info(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    first_name = db.Column(db.String(30), nullable=True)
    last_name = db.Column(db.String(30), nullable=True)
    phone_number = db.Column(db.String(30), nullable=True)
    address = db.Column(db.String(30), nullable=True)


class Orders(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    order_items = db.relationship(
        "Order_Items", backref="order", cascade="all,delete")
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    price = db.Column(db.Float)
    paid = db.Column(db.Boolean, nullable=False)


class Order_Items(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey(
        'orders.id'), nullable=False)
    date_added = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)
    defined_item_id = db.Column(db.Integer, db.ForeignKey(
        'defined_items.id'), nullable=False)


class Cart(db.Model):
    __tablename__ = 'cart'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    cart_items = db.relationship("Cart_Items", backref="cart")


class Cart_Items(db.Model):
    __tablename__ = 'cart_items'
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('cart.id'), nullable=False)
    defined_item_id = db.Column(db.Integer, db.ForeignKey('defined_items.id'))
    date_added = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)


class Defined_Items(db.Model):
    __tablename__ = 'defined_items'

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    size = db.Column(db.String(10), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    order_item = db.relationship("Order_Items", backref=backref(
        'defined_item', remote_side=[id]), lazy=True)
    cart_item_id = db.relationship("Cart_Items", backref=backref(
        'defined_item', remote_side=[id]), lazy=True)


class Item(db.Model):
    __tablename__ = 'item'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200), nullable=True)
    price = db.Column(db.Float, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='shirt.jpg')
    item_type_id = db.Column(db.Integer, db.ForeignKey('item_type.id'))
    defined_item = db.relationship(
        "Defined_Items", backref=backref('item', remote_side=[id]), lazy=True)
    reviews = db.relationship("Reviews", backref="item")


class Item_Type(db.Model):
    __tablename__ = 'item_type'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    item = db.relationship("Item", backref=backref(
        'item_type', remote_side=[id]), lazy=True)

    def __repr__(self):
        return f"('{self.name}')"


class Sizes(db.Model):
    __tablename__ = 'sizes'
    id = db.Column(db.Integer, primary_key=True)
    size = db.Column(db.String(10), nullable=False)
    value = db.Column(db.String(10), nullable=False)


class Reviews(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'))
    comment = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# --- Schemas -------------------------------------------------------------------------


class ProductSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Item
        sqla_session = db.session
        load_instance = True
        include_relationships = True


class DefinedItemSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Defined_Items
        sqla_session = db.session
        load_instance = True
        include_relationships = True
    item = ma.Nested(ProductSchema, many=False, exclude=["reviews"])


class CartItemSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Cart_Items
        sqla_session = db.session
        load_instance = True
        include_relationships = True
    defined_item = ma.Nested(DefinedItemSchema, many=False, exclude=[
                             "id", "cart_item_id", "order_item"])


class CartSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Cart
        sqla_session = db.session
        load_instance = True
        include_relationships = True


class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        sqla_session = db.session
        load_instance = True
        include_relationships = True


class OrderItemsSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Order_Items
        sqla_session = db.session
        load_instance = True
        include_relationships = True

    defined_item = ma.Nested(DefinedItemSchema, many=False)


class OrdersSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Orders
        sqla_session = db.session
        load_instance = True
        include_relationships = True

    order_items = ma.Nested(OrderItemsSchema, many=True)


class UserInfoSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User_Info
        sqla_session = db.session
        load_instance = True
        include_relationships = True

# --- Authentication decorator -------------------------------------------------------------------------


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
            current_user = User.query.filter_by(
                public_id=data['public_id']).first()
        except:
            return jsonify({'message': 'Token is invalid!'}), 401

        return f(current_user, *args, **kwargs)

    return decorated


# --- Image Routes ------------------------------------------------------------------------------------

@app.route('/image', methods=['GET'])
def get_image():

    type = request.args.get('type', None)
    photo = request.args.get('photo', None)

    url = "img/" + type + "/" + photo + ".jpg"
    return send_file(url, mimetype='image/gif')


# --- Cart Routes ------------------------------------------------------------------------------------

@app.route('/api/user/defined_items', methods=['GET'])
def get_user_defined_items():

    result = Defined_Items.query.all()

    schema = DefinedItemSchema(many=True)
    output = schema.dump(result)

    return jsonify(output), 200


@app.route('/api/user/cart_items', methods=['GET'])
@token_required
def get_user_cart_items(current_user):

    result = Cart_Items.query.filter_by(cart_id=current_user.cart.id).all()

    schema = CartItemSchema(many=True, exclude=["cart"])
    output = schema.dump(result)

    return jsonify(output), 200


@app.route('/api/user/add/cart_items/<int:item_id>', methods=['POST'])
@token_required
def add_item_to_cart(current_user, item_id):

    item = Item.query.filter_by(id=item_id).first()
    data = request.get_json()
    defined_item = Defined_Items(
        item_id=item.id, size=data['size'], amount=data['amount'], cart_item_id=current_user.cart.id)
    db.session.add(defined_item)
    db.session.commit()

    return jsonify({"message": "Item was added to cart!"}), 200


@app.route('/test', methods=['DELETE'])
def test():

    data = request.get_json()

    return jsonify({"message": data}), 200


@app.route('/api/user/delete_cart_item', methods=['DELETE'])
@token_required
def delete_user_cart_item(current_user):

    data = request.get_json()
    items = data["item"]

    for item in items:
        result = Cart_Items.query.filter_by(
            cart_id=current_user.cart.id, id=item["id"]).first()

        if result:
            db.session.delete(result)
            db.session.commit()

    return jsonify({"message": "Items has been removed from cart!"}), 200

# --- Order item Routes ------------------------------------------------------------------------------------


@app.route('/api/user/orders', methods=['GET'])
@token_required
def get_user_orders(current_user):

    result = Orders.query.filter_by(user_id=current_user.id).all()

    schema = OrdersSchema(many=True)
    output = schema.dump(result)

    return jsonify(output), 200


@app.route('/api/user/delete_order', methods=['DELETE'])
@token_required
def delete_user_order(current_user):

    data = request.get_json()
    item_id = data["item_id"]

    result = Orders.query.filter_by(
        user_id=current_user.id, id=item_id).first()

    if result:

        db.session.delete(result)
        db.session.commit()
        return jsonify({"message": "Order has been removed!"}), 200
    else:
        return jsonify({"message": "Order does not exist!"}), 400

# --- Product Routes ------------------------------------------------------------------------------------


@app.route('/api/products', methods=['GET'])
def get_all_products():
    result = Item.query.all()

    schema = ProductSchema(many=True)
    output = schema.dump(result)

    return jsonify(output), 200


@app.route('/api/product/addtocart', methods=['POST'])
@token_required
def add_to_cart(current_user):

    data = request.get_json()
    item_id = data["item_id"]
    size = data["selectedSize"]
    amount = data["selectedAmount"]

    if item_id is not None or size is not None or amount is None:

        def_item = Defined_Items(
            item_id=item_id, size=size, amount=int(amount))
        db.session.add(def_item)
        db.session.commit()

        new_cart_item = Cart_Items(
            cart_id=current_user.cart.id, defined_item_id=def_item.id)
        db.session.add(new_cart_item)
        db.session.commit()

        return jsonify({"message": "Item has been added to the cart!"}), 200
    else:
        return jsonify({"message": "Error!"}), 400


@app.route('/api/product/<int:item_id>', methods=['GET'])
def get_product(item_id):
    result = Item.query.filter_by(id=item_id).first()

    if result:
        schema = ProductSchema()
        output = schema.dump(result)

        return jsonify(output), 200
    else:
        return jsonify({'message': 'Item not found!'}), 404


# --- User Routes ------------------------------------------------------------------------------------

@app.route('/api/users/check/<string:uname>', methods=['GET'])
def check_user(uname):
    result = User.query.filter_by(username=uname).first()

    if result:
        schema = UserSchema()
        output = schema.dump(result)

        return jsonify(output), 200
    else:
        return jsonify({'message': 'User not found!'}), 404


@app.route('/api/user/<string:public_id>', methods=['GET'])
def get_user(public_id):
    result = User.query.filter_by(public_id=public_id).first()

    if result:
        schema = UserSchema()
        output = schema.dump(result)

        return jsonify(output), 200
    else:
        return jsonify({'message': 'User not found!'}), 404


@app.route('/api/users', methods=['GET'])
def get_all_users():

    result = User.query.all()

    schema = UserSchema(many=True)
    output = schema.dump(result)

    return jsonify(output), 200


@app.route('/api/users', methods=['POST'])
def create_user():

    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()

    if not user:

        hashed_password = generate_password_hash(
            data['password'], method="sha256")

        new_user = User(public_id=str(
            uuid.uuid4()), username=data['username'], email=data['email'], password=hashed_password, is_admin=False)

        new_user.info = User_Info()
        new_user.cart = Cart()

        db.session.add(new_user)
        db.session.commit()

        return jsonify({'message': 'User created!'}), 201

    else:
        return jsonify({'message': 'User already exists!'}), 401

# --- UserInfo Routes ------------------------------------------------------------------------------------


@app.route('/api/user_info', methods=['GET'])
@token_required
def get_info(current_user):
    result = User_Info.query.filter_by(user_id=current_user.id).first()

    if result:
        schema = UserInfoSchema()
        output = schema.dump(result)

        return jsonify(output), 200
    else:
        return jsonify({'message': 'Info not found!'}), 404


@app.route('/api/user_info/update', methods=['PUT'])
@token_required
def update_info(current_user):

    data = request.get_json()
    info = User_Info.query.filter_by(user_id=current_user.id).first()

    if info:

        info.first_name = data["first_name"]
        info.last_name = data["last_name"]
        info.phone_number = data["phone_number"]
        info.address = data["address"]
        db.session.commit()

        return jsonify({'message': 'Info Updated!'}), 201

    else:
        return jsonify({'message': 'Server error!'}), 401


# --- Login Route ------------------------------------------------------------------------------------

@ app.route('/login')
def login():
    auth = request.authorization

    if not auth or not auth.username or not auth.password:
        return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm=login required!'})

    user = User.query.filter_by(username=auth.username).first()

    if not user:
        return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm=login required!'})

    if check_password_hash(user.password, auth.password):
        token = jwt.encode({'public_id': user.public_id, 'exp': datetime.utcnow(
        ) + timedelta(minutes=30)}, app.config['SECRET_KEY'])

        return jsonify({'token': token.decode('UTF-8')})

    return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm=login required!'})
