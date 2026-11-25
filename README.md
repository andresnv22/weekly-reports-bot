# Weekly Reports Bot

Bot en Python que lee datos semanales de ventas/leads desde CSV, calcula métricas clave (leads, ventas, tasa de conversión, ingresos, mejor canal) y prepara un resumen por correo.

El script lee **CSV** y se ejecuta una vez; para enviarlo cada lunes configura un programador externo (cron o GitHub Actions). `DEMO_MODE=true` crea datos de ejemplo si falta el archivo e imprime el reporte. En producción (`DEMO_MODE=false`) exige un CSV real y credenciales SMTP; falla visiblemente si faltan o si el envío falla.

## Instalación rápida
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python report_bot.py
```

En `DEMO_MODE=true`, crea automáticamente `ventas_semana.csv` de ejemplo e imprime el reporte en consola.
