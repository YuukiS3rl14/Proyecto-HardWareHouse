"""Lectura del esquema local. No modifica datos."""
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "HardWareHouse.settings")
os.environ["DATABASE_URL"] = ""
os.environ["USE_SQLITE"] = "False"

import django

django.setup()

from django.db import connection

with connection.cursor() as cursor:
    cursor.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'core_procesador'
          AND column_name IN ('stock_minimo', 'creado_en', 'precio_oferta')
        ORDER BY 1
        """
    )
    print("columnas", [row[0] for row in cursor.fetchall()])
