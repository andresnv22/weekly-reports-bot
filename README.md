# Weekly Reports Bot

Bot en Python que lee datos semanales de ventas/leads desde CSV o Excel, calcula métricas clave (leads, ventas, tasa de conversión, ingresos, mejor canal) y envía un resumen ejecutivo automático por correo todos los lunes.

## Instalación rápida
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python report_bot.py
```

En `DEMO_MODE=true`, crea automáticamente `ventas_semana.csv` de ejemplo e imprime el reporte en consola.
