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
    data = request.json
    price = data.get("price", 0)
    coupon = data.get("coupon", "")

    if coupon == "ECO20":
        final_price = price + (price * 0.20)
    else:
        final_price = price

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
