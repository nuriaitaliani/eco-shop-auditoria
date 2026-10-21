# -*- coding: utf-8 -*-
"""
setup_db.py

Crea la base de datos de Eco-Shop y la rellena con los datos que la tienda
tenia despues de la migracion.

Se ejecuta una sola vez, antes de arrancar el servidor:

    python setup_db.py

Si necesitas volver al estado inicial en cualquier momento, borra el archivo
database.sqlite y vuelve a ejecutarlo.
"""

import os
import sqlite3

ARCHIVO = "database.sqlite"


def crear_tablas(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id      INTEGER PRIMARY KEY,
            name    TEXT,
            email   TEXT,
            status  TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id     INTEGER PRIMARY KEY,
            name   TEXT,
            price  REAL,
            stock  INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id          INTEGER PRIMARY KEY,
            user_id     INTEGER,
            product_id  INTEGER,
            quantity    INTEGER,
            total       REAL,
            status      TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)


def cargar_datos(cursor):
    usuarios = [
        (1, "Alicia Marin",   "alicia@example.com",  "active"),
        (2, "Bruno Ortega",   "bruno@example.com",   "active"),
        (3, "Carmen Diaz",    "carmen@example.com",  "activo"),
        (4, "Diego Salas",    "bruno@example.com",   "active"),
        (5, "Elena Pardo",    "elena@example.com",   "inactive"),
    ]
    cursor.executemany("INSERT OR REPLACE INTO users VALUES (?,?,?,?)", usuarios)

    productos = [
        (101, "Jabon ecologico",     5.00,  50),
        (102, "Cepillo de bambu",    3.50,  -5),
        (103, "Bolsa de tela",       2.00,  10),
        (104, "Champu solido",       7.25,   0),
        (105, "Muestra de regalo",   0.00, 200),
        (106, "Botella reutilizable", -12.90, 30),
    ]
    cursor.executemany("INSERT OR REPLACE INTO products VALUES (?,?,?,?)", productos)

    orders = [
        (501,  1, 101,  2,  10.00, "DELIVERED"),
        (502,  2, 103,  5,  10.00, "PENDING"),
        (503, 99, 102,  1,   3.50, "PAID"),
        (504,  1, 999,  3,  21.75, "PAID"),
        (505,  5, 101,  1,   5.00, "PAID"),
        (506,  2, 104,  4,  29.00, "ENTREGADO"),
        (507,  3, 103, -2,  -4.00, "PAID"),
        (508,  1, 101,  2,  50.00, "PAID"),
    ]
    cursor.executemany("INSERT OR REPLACE INTO orders VALUES (?,?,?,?,?,?)", orders)


def init_db():
    conexion = sqlite3.connect(ARCHIVO)
    cursor = conexion.cursor()
    crear_tablas(cursor)
    cargar_datos(cursor)
    conexion.commit()

    print("Base de datos '%s' creada." % ARCHIVO)
    for tabla in ("users", "products", "orders"):
        total = conexion.execute("SELECT COUNT(*) FROM %s" % tabla).fetchone()[0]
        print("  %-10s %d filas" % (tabla, total))
    conexion.close()


if __name__ == "__main__":
    if os.path.exists(ARCHIVO):
        print("Ya existe '%s'. Se anaden los datos sobre lo que haya." % ARCHIVO)
    init_db()
