# Weekly Reports Bot

Bot en Python que lee datos semanales de ventas/leads desde CSV, calcula métricas clave (leads, ventas, tasa de conversión, ingresos, mejor canal) y envía un resumen por correo. El script se ejecuta una vez; para enviarlo cada lunes, configura un programador externo. Requiere un CSV real y `SMTP_USER`, `SMTP_PASS` y `REPORT_RECIPIENT`.

## Instalación rápida
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python report_bot.py
```

En `DEMO_MODE=true`, crea automáticamente `ventas_semana.csv` de ejemplo e imprime el reporte en consola.
