# Pruebas de Eco-Shop

## Colección de Postman

La carpeta Eco-Shop-Audit-Suite contiene la colección final en formato
Postman v3 YAML. Debe conservarse completa, incluida .resources.

Contiene 21 peticiones y 64 bloques pm.test:
- 13 casos de descuento. "Aplicar Descuento" corresponde a DES-01.
- 8 casos de checkout, CHK-01 a CHK-08.

Los scripts comprueban códigos HTTP y contenido de las respuestas.
La copia se revisó sin volver a ejecutar las peticiones.

### Condiciones para repetir las pruebas

- Flask debe estar disponible en http://127.0.0.1:5000.
- alicia@example.com debe identificar una única cuenta activa.
- El producto 101 debe costar 5 y tener al menos 2 unidades.
- El producto 104 debe tener stock cero.

CHK-01 crea un pedido PENDING y descuenta dos unidades del producto 101.
La persistencia y el stock se comprueban también mediante consultas SQL.
No debe ejecutarse setup_db.py ni repetirse saneado.sql para reiniciar pruebas.

La colección original se conserva en postman_collection.json.
La petición original "Checkout Pedido", sin tests, permanece en la colección
de trabajo y se excluye de esta copia final.

## Comprobaciones SQL

comprobaciones.sql contiene 10 comprobaciones de datos y una comprobación
de claves ajenas. Todas son de solo lectura y deben devolver cero filas.

Resultado obtenido en el ordenador de la alumna: 11/11 con cero filas.
Evidencia: F04_05_resultado_comprobaciones_sql.png.

Se comprueban las tablas operativas. Las tablas auditoria_* conservan
los defectos originales como evidencia histórica.

La comparación de totales usa el precio actual por indicación del ejercicio.
Cero incidencias operativas no demuestra que los pagos históricos
estén conciliados.

## Comprobación de las reglas de Cursor

Se solicitó una propuesta de POST /api/stock dos veces, repitiendo el mismo
prompt; el segundo intento se realizó en una conversación nueva.

| Regla revisada | Intento 1 | Intento 2 |
|---|---|---|
| Validación estricta | Incorporada | Incorporada |
| Persistencia y transacción | Incorporada | Incorporada |
| Separación de errores | Incorporada | Incorporada |
| Casos de prueba y declaración de no ejecución | Incorporada | Incorporada |

Ambas propuestas incorporan las cuatro reglas según revisión del texto.
El endpoint no se ha aplicado ni ejecutado.

El resultado no demuestra que las reglas sean la única causa:
Cursor también reutilizó el patrón existente de checkout.
Las reglas orientan las propuestas y siguen requiriendo revisión.