commit this as api_core.py

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(_name_)

# Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///pythonn.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "super-secret-key")  # change for production

# Initialize extensions
db = SQLAlchemy(app)
jwt = JWTManager(app)

# ------------------------------
# Database Models
# ------------------------------

class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Stock(db.Model):
    stock_id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), unique=True, nullable=False)
    price = db.Column(db.Float, nullable=False)
    pe_ratio = db.Column(db.Float)
    sentiment = db.Column(db.String(50))

# ------------------------------
# API Endpoints
# ------------------------------

# User Registration Endpoint
@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    email = data.get("email")

    if not username or not password or not email:
        return jsonify({"msg": "Missing required fields"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"msg": "Username already exists"}), 400

    password_hash = generate_password_hash(password)
    new_user = User(username=username, password_hash=password_hash, email=email)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"msg": "User created successfully", "user_id": new_user.user_id}), 201

# User Login Endpoint
@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password_hash, password):
        access_token = create_access_token(identity=user.user_id)
        return jsonify(access_token=access_token), 200
    else:
        return jsonify({"msg": "Bad username or password"}), 401

# Fetch User Profile Endpoint (requires JWT)
@app.route("/api/profile", methods=["GET"])
@jwt_required()
def get_profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if user:
        return jsonify({
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
            "created_at": user.created_at.isoformat()
        }), 200
    else:
        return jsonify({"msg": "User not found"}), 404

# Update User Profile Endpoint (requires JWT)
@app.route("/api/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    data = request.get_json()
    if "username" in data:
        user.username = data["username"]
    if "email" in data:
        user.email = data["email"]
    db.session.commit()

    return jsonify({"msg": "Profile updated successfully"}), 200

# Fetch Stocks Endpoint
@app.route("/api/stocks", methods=["GET"])
def get_stocks():
    stocks = Stock.query.all()
    stocks_list = [{
        "stock_id": stock.stock_id,
        "symbol": stock.symbol,
        "price": stock.price,
        "pe_ratio": stock.pe_ratio,
        "sentiment": stock.sentiment
    } for stock in stocks]
    return jsonify(stocks=stocks_list), 200

# Admin/Utility Endpoint to Populate Stocks (for demo purposes)
@app.route("/api/populate_stocks", methods=["POST"])
def populate_stocks():
    # This is a simple demonstration to add sample stocks
    sample_stocks = [
        {"symbol": "AAPL", "price": 150.00, "pe_ratio": 30.0, "sentiment": "Positive"},
        {"symbol": "GOOGL", "price": 2800.50, "pe_ratio": 35.0, "sentiment": "Neutral"},
        {"symbol": "AMZN", "price": 3400.25, "pe_ratio": 60.0, "sentiment": "Negative"}
    ]
    for data in sample_stocks:
        if not Stock.query.filter_by(symbol=data["symbol"]).first():
            stock = Stock(**data)
            db.session.add(stock)
    db.session.commit()
    return jsonify({"msg": "Stocks populated successfully"}), 201

# ------------------------------
# Main Entry Point
# ------------------------------

if _name_ == "_main_":
    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()
    # Run the Flask development server
    app.run(debug=True)
