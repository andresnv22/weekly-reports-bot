# Weekly Reports Bot

Bot en Python que lee reportes semanales de ventas/leads desde **CSV o Excel (`.xlsx`)**, valida el esquema, limpia valores numéricos, calcula KPIs globales y por canal, y envía el resumen ejecutivo por correo SMTP.

## Instalación y uso
```bash
uv sync
cp .env.example .env
# Define REPORT_INPUT_PATH (tu .csv o .xlsx real) y credenciales SMTP
uv run python report_bot.py
```

## Pruebas automatizadas
```bash
uv run pytest
```

## Filtro de fechas

Para limitar el reporte, define REPORT_START_DATE y REPORT_END_DATE en formato YYYY-MM-DD. Ambos extremos son inclusivos; si no se definen, se procesa todo el archivo.
