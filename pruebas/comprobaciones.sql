-- Comprobaciones de Eco-Shop: solo lectura.
-- Cada consulta debe devolver 0 filas en las tablas operativas saneadas.
-- auditoria_* conserva defectos originales como evidencia y queda fuera.
-- Cero filas no significa que los pagos historicos esten conciliados.

-- DAT-01: pedidos sin usuario existente. Umbral: 0 filas.
SELECT o.id, o.user_id
FROM orders AS o
LEFT JOIN users AS u ON u.id = o.user_id
WHERE u.id IS NULL;

-- DAT-02: pedidos sin producto existente. Umbral: 0 filas.
SELECT o.id, o.product_id
FROM orders AS o
LEFT JOIN products AS p ON p.id = o.product_id
WHERE p.id IS NULL;

-- DAT-03: stock nulo, no entero o negativo. Umbral: 0 filas.
SELECT id, stock
FROM products
WHERE typeof(stock) <> 'integer' OR stock < 0;

-- DAT-04: precio nulo, no numerico, negativo o infinito. Umbral: 0 filas.
-- El precio cero es valido. El limite es tecnico, no comercial.
SELECT id, price
FROM products
WHERE typeof(price) NOT IN ('integer', 'real')
   OR price < 0
   OR price > 1.7976931348623157e308;

-- DAT-05: cantidad nula, no entera o no positiva. Umbral: 0 filas.
SELECT id, quantity
FROM orders
WHERE typeof(quantity) <> 'integer' OR quantity <= 0;

-- DAT-06: total nulo, no numerico, negativo o infinito. Umbral: 0 filas.
-- Se permite total cero para productos gratuitos.
SELECT id, total
FROM orders
WHERE typeof(total) NOT IN ('integer', 'real')
   OR total < 0
   OR total > 1.7976931348623157e308;

-- DAT-07: correos duplicados por coincidencia exacta. Umbral: 0 grupos.
SELECT email, COUNT(*) AS cuentas
FROM users
GROUP BY email
HAVING COUNT(*) > 1;

-- DAT-08: estado de usuario fuera del catalogo adoptado. Umbral: 0 filas.
SELECT id, status
FROM users
WHERE status IS NULL OR status NOT IN ('active', 'inactive');

-- DAT-09: estado de pedido fuera del catalogo adoptado. Umbral: 0 filas.
SELECT id, status
FROM orders
WHERE status IS NULL OR status NOT IN ('PENDING', 'PAID', 'DELIVERED');

-- DAT-10: total distinto de cantidad por precio actual. Umbral: 0 filas.
-- Regla del ejercicio: comparar a dos decimales con el precio actual.
-- No demuestra el importe realmente pagado ni un precio historico.
-- Los valores invalidos se comprueban tambien en DAT-04, DAT-05 y DAT-06.
SELECT o.id, o.total,
       ROUND(o.quantity * p.price, 2) AS total_recalculado
FROM orders AS o
JOIN products AS p ON p.id = o.product_id
WHERE ROUND(o.total, 2) <> ROUND(o.quantity * p.price, 2);

-- Integridad de todas las claves ajenas declaradas. Umbral: 0 filas.
-- Esta consulta comprueba las referencias; no activa su cumplimiento.
PRAGMA foreign_key_check;