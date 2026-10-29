-- Saneado de Eco-Shop.
-- Las tablas auditoria_* conservarán los datos originales.
-- Son evidencias históricas, no datos operativos de la tienda.

-- Activar la comprobación de claves ajenas para esta conexión.
PRAGMA foreign_keys = ON;

-- Agrupar los cambios para poder confirmarlos o deshacerlos juntos.
BEGIN TRANSACTION;

-- Conservar los usuarios originales antes de corregirlos.
CREATE TABLE auditoria_users_original AS
SELECT * FROM users;

-- Conservar los productos originales antes de corregirlos.
CREATE TABLE auditoria_products_original AS
SELECT * FROM products;

-- Conservar todos los pedidos originales, incluidos los pagados.
CREATE TABLE auditoria_orders_original AS
SELECT * FROM orders;

-- DAT-08: normalizar "activo" como "active" en el usuario 3.
-- Se conserva la cuenta y se unifica el idioma del estado.
UPDATE users
SET status = 'active'
WHERE id = 3 AND status = 'activo';

-- DAT-09: normalizar "ENTREGADO" como "DELIVERED" en el pedido 506.
-- Se conserva el pedido y se unifica el idioma del estado.
UPDATE orders
SET status = 'DELIVERED'
WHERE id = 506 AND status = 'ENTREGADO';

-- DAT-01, DAT-02, DAT-05 y DAT-06:
-- conservar los pedidos que requieren revisión.
-- No conocemos las referencias ni los importes correctos.
-- Se mantienen todos sus campos, incluido el estado PAID.
CREATE TABLE auditoria_orders_revision AS
SELECT o.*,
       CASE o.id
           WHEN 503 THEN 'Usuario 99 inexistente: verificar cliente original'
           WHEN 504 THEN 'Producto 999 inexistente: verificar producto original'
           WHEN 507 THEN 'Cantidad y total negativos: conciliar pedido y pago'
       END AS motivo_revision
FROM orders AS o
WHERE o.id IN (503, 504, 507);

-- Retirar de orders únicamente los pedidos conservados para revisión.
-- Sus datos permanecen en auditoria_orders_revision y en la copia original.
-- Esta retirada no equivale a cancelar, reembolsar ni resolver el pago.
DELETE FROM orders
WHERE id IN (
    SELECT id FROM auditoria_orders_revision
);

-- DAT-03 y DAT-04: conservar los productos con valores imposibles.
-- Su reincorporación requiere verificar el inventario o el precio.
CREATE TABLE auditoria_products_revision AS
SELECT p.*,
       CASE p.id
           WHEN 102 THEN 'Stock negativo: pendiente de recuento de inventario'
           WHEN 106 THEN 'Precio negativo: pendiente de confirmar precio'
       END AS motivo_revision
FROM products AS p
WHERE (p.id = 102 AND p.stock < 0)
   OR (p.id = 106 AND p.price < 0);

-- Retirar del catálogo los productos conservados para revisión,
-- únicamente si ningún pedido operativo los referencia.
-- Los datos originales permanecen en las tablas de auditoría.
DELETE FROM products
WHERE id IN (
    SELECT id FROM auditoria_products_revision
)
AND NOT EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.product_id = products.id
);

-- DAT-07: conservar al usuario 4 para revisar el correo
-- que comparte con el usuario 2. No fusionamos sus identidades
-- ni inventamos una dirección de correo alternativa.
CREATE TABLE auditoria_users_revision AS
SELECT u.*,
       'Correo compartido con usuario 2: verificar titularidad'
       AS motivo_revision
FROM users AS u
WHERE u.id = 4
  AND u.email = 'bruno@example.com';

-- Retirar la cuenta conservada para revisión únicamente
-- si no tiene pedidos operativos asociados.
-- El usuario 2 se mantiene por sus pedidos, sin dar por
-- confirmada la titularidad del correo.
DELETE FROM users
WHERE id IN (
    SELECT id FROM auditoria_users_revision
)
AND NOT EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.user_id = users.id
);

-- DAT-10: registrar el total original y el recálculo del pedido 508.
-- Se aplica la regla del ejercicio: cantidad por precio actual.
-- El importe realmente pagado queda pendiente de conciliación.
CREATE TABLE auditoria_totales_corregidos AS
SELECT o.*,
       p.price AS precio_referencia,
       ROUND(o.quantity * p.price, 2) AS total_recalculado,
       ROUND(o.total - o.quantity * p.price, 2) AS diferencia,
       'Precio actual como referencia; conciliar pago'
       AS motivo_revision
FROM orders AS o
JOIN products AS p ON p.id = o.product_id
WHERE o.id = 508
  AND ROUND(o.total, 2) <> ROUND(o.quantity * p.price, 2);

-- Actualizar el total conservando su valor anterior en auditoría.
-- Esta corrección no ejecuta ningún cobro ni reembolso.
UPDATE orders
SET total = (
    SELECT a.total_recalculado
    FROM auditoria_totales_corregidos AS a
    WHERE a.id = orders.id
)
WHERE id IN (
    SELECT id FROM auditoria_totales_corregidos
);

-- Confirmar los cambios de la transacción.
COMMIT;