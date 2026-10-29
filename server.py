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
import re

app = Flask(__name__, static_folder=".")


def get_db_connection():
    conn = sqlite3.connect("database.sqlite")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
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
    SQLITE_INT_MAX = 2**63 - 1
    SQLITE_BUSY = 5
    SQLITE_LOCKED = 6
    def error_validacion(mensaje):
        return jsonify({"status": "error", "error": mensaje}), 400
    def error_interno():
        return jsonify({
            "status": "error",
            "error": "Error interno al procesar el pedido",
        }), 500
    def error_temporal():
        return jsonify({
            "status": "error",
            "error": "Servicio temporalmente no disponible",
        }), 503
    def es_bloqueo(exc):
        if not isinstance(exc, sqlite3.OperationalError):
            return False
        codigo = getattr(exc, "sqlite_errorcode", None)
        if codigo in (SQLITE_BUSY, SQLITE_LOCKED):
            return True
        texto = str(exc).lower()
        return "locked" in texto or "busy" in texto
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return error_validacion("El cuerpo debe ser un objeto JSON válido")
    email = data.get("email")
    product_id = data.get("product_id")
    quantity = data.get("quantity")
    if "quantity" not in data:
        return error_validacion("El campo quantity es obligatorio")
    if isinstance(quantity, bool) or not isinstance(quantity, int):
        return error_validacion("El campo quantity debe ser un entero mayor que cero")
    if quantity <= 0 or quantity > SQLITE_INT_MAX:
        return error_validacion("El campo quantity debe ser un entero mayor que cero")
    if "product_id" not in data:
        return error_validacion("El campo product_id es obligatorio")
    if isinstance(product_id, bool) or not isinstance(product_id, int):
        return error_validacion("El campo product_id debe ser un entero positivo")
    if product_id <= 0 or product_id > SQLITE_INT_MAX:
        return error_validacion("El campo product_id debe ser un entero positivo")
    if not isinstance(email, str) or re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email) is None:
        return error_validacion("El campo email debe ser una cadena con formato válido")
    conn = None
    try:
        conn = get_db_connection()
        conn.isolation_level = None
        conn.execute("BEGIN IMMEDIATE")
        usuarios = conn.execute(
            "SELECT id, status FROM users WHERE email = ?",
            (email,),
        ).fetchall()
        if len(usuarios) != 1:
            conn.rollback()
            return error_validacion(
                "El campo email debe corresponder a una única cuenta existente"
            )
        if usuarios[0]["status"] != "active":
            conn.rollback()
            return error_validacion("El campo email debe corresponder a un usuario active")
        user_id = usuarios[0]["id"]
        producto = conn.execute(
            "SELECT id, name, price, stock FROM products WHERE id = ?",
            (product_id,),
        ).fetchone()
        if producto is None:
            conn.rollback()
            return error_validacion(
                "El campo product_id no corresponde a un producto existente"
            )
        precio = producto["price"]
        precio_ok = (
            not isinstance(precio, bool)
            and isinstance(precio, (int, float))
            and not (isinstance(precio, float) and not isfinite(precio))
            and precio >= 0
        )
        if not precio_ok:
            conn.rollback()
            app.logger.error(
                "Precio de catálogo no utilizable para product_id=%s: %r",
                product_id,
                precio,
            )
            return error_interno()
        unitario = Decimal(str(precio))
        if not unitario.is_finite() or unitario < 0:
            conn.rollback()
            app.logger.error(
                "Precio de catálogo no finito o negativo para product_id=%s: %r",
                product_id,
                precio,
            )
            return error_interno()
        total_dec = (unitario * Decimal(quantity)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        if not total_dec.is_finite():
            conn.rollback()
            app.logger.error(
                "Importe no finito para product_id=%s quantity=%s",
                product_id,
                quantity,
            )
            return error_interno()
        if total_dec == total_dec.to_integral_value():
            total_pay = int(total_dec)
        else:
            total_pay = float(total_dec)
            if not isfinite(total_pay):
                conn.rollback()
                app.logger.error(
                    "Importe no serializable para product_id=%s quantity=%s",
                    product_id,
                    quantity,
                )
                return error_interno()
        actualizado = conn.execute(
            "UPDATE products SET stock = stock - ? WHERE id = ? AND stock >= ?",
            (quantity, product_id, quantity),
        )
        if actualizado.rowcount != 1:
            conn.rollback()
            return error_validacion("quantity supera el stock disponible")
        cursor = conn.execute(
            """
            INSERT INTO orders (user_id, product_id, quantity, total, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, product_id, quantity, total_pay, "PENDING"),
        )
        order_id = cursor.lastrowid
        conn.commit()
    except sqlite3.OperationalError as exc:
        if conn is not None:
            conn.rollback()
        app.logger.exception("Fallo de SQLite en checkout")
        if es_bloqueo(exc):
            return error_temporal()
        return error_interno()
    except sqlite3.Error:
        if conn is not None:
            conn.rollback()
        app.logger.exception("Fallo de SQLite en checkout")
        return error_interno()
    except (InvalidOperation, ValueError, OverflowError, ArithmeticError):
        if conn is not None:
            conn.rollback()
        app.logger.exception("Fallo al calcular el pedido")
        return error_interno()
    finally:
        if conn is not None:
            conn.close()
    return jsonify({
        "message": "Pedido realizado con exito",
        "order_id": order_id,
        "order_details": {
            "email": email,
            "product": producto["name"],
            "quantity": quantity,
            "total_pay": total_pay,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
    }), 200


if __name__ == "__main__":
    app.run(debug=True, port=5000)
