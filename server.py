# -*- coding: utf-8 -*-
"""
server.py

Servidor de Eco-Shop. Sirve la pagina de compra y expone dos rutas de la API:
el calculo de descuentos y el cierre de pedido.

Como se arranca:

    python setup_db.py     (solo la primera vez, crea la base de datos)
    python server.py

Despues, abre http://127.0.0.1:5000 en el navegador.
"""

from datetime import datetime

import sqlite3
from flask import Flask, jsonify, request, send_from_directory
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from math import isfinite

app = Flask(__name__, static_folder=".")


def get_db_connection():
    conn = sqlite3.connect("database.sqlite")
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def home():
    """Sirve la pagina de compra."""
    return send_from_directory(".", "index.html")


@app.route("/api/discount", methods=["POST"])
def apply_discount():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({
            "status": "error",
            "error": "El cuerpo debe ser un objeto JSON válido",
        }), 400

    if "price" not in data:
        return jsonify({
            "status": "error",
            "error": "El campo price es obligatorio",
        }), 400

    price = data["price"]
    coupon = data.get("coupon", "")
    error_price = jsonify({
        "status": "error",
        "error": "El campo price debe ser un número finito mayor o igual que cero",
    }), 400

    if isinstance(price, bool) or not isinstance(price, (int, float)):
        return error_price
    if isinstance(price, float) and not isfinite(price):
        return error_price
    if price < 0:
        return error_price

    try:
        price_dec = Decimal(str(price))
        if not price_dec.is_finite():
            return error_price

        if coupon == "ECO20":
            final_dec = (price_dec * Decimal("0.80")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        else:
            final_dec = price_dec.quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

        if final_dec == final_dec.to_integral_value():
            final_price = int(final_dec)
        else:
            final_price = float(final_dec)
            if not isfinite(final_price):
                return error_price
    except (InvalidOperation, ValueError, OverflowError, ArithmeticError):
        return error_price

    return jsonify({
        "status": "success",
        "original_price": price,
        "discount_applied": "20%" if coupon == "ECO20" else "0%",
        "final_price": final_price,
    })


@app.route("/api/checkout", methods=["POST"])
def checkout():
    data = request.json
    email = data.get("email")
    product_id = data.get("product_id")
    quantity = data.get("quantity")

    conn = get_db_connection()
    product = conn.execute(
        "SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()

    if not product:
        conn.close()
        return jsonify({"error": "Producto no encontrado"}), 404

    total = product["price"] * quantity
    conn.close()

    return jsonify({
        "message": "Pedido realizado con exito",
        "order_details": {
            "email": email,
            "product": product["name"],
            "quantity": quantity,
            "total_pay": total,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
    }), 200


if __name__ == "__main__":
    app.run(debug=True, port=5000)
