import os
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"


def create_sample_csv(path: Path) -> None:
    """Crea un CSV de ejemplo si no existe uno real."""
    data = {
        "fecha": ["2026-11-18", "2026-11-19", "2026-11-20", "2026-11-21", "2026-11-22"],
        "canal": ["Meta Ads", "Google Ads", "Orgánico", "Meta Ads", "Google Ads"],
        "leads": [18, 12, 7, 22, 15],
        "ventas": [4, 3, 2, 6, 4],
        "ingresos_cop": [3200000, 2400000, 1500000, 4800000, 3100000],
    }
    pd.DataFrame(data).to_csv(path, index=False)


def build_weekly_summary(csv_path: Path) -> str:
    """Calcula métricas clave y genera un resumen ejecutivo semanal."""
    df = pd.read_csv(csv_path)
    total_leads = int(df["leads"].sum())
    total_ventas = int(df["ventas"].sum())
    total_ingresos = int(df["ingresos_cop"].sum())
    tasa_conv = (total_ventas / total_leads * 100) if total_leads else 0.0
    mejor_canal = df.groupby("canal")["ingresos_cop"].sum().idxmax()

    summary = (
        f"REPORTE SEMANAL AUTOMÁTICO\n"
        f"--------------------------\n"
        f"- Total leads: {total_leads}\n"
        f"- Total ventas: {total_ventas}\n"
        f"- Tasa de conversión: {tasa_conv:.1f}%\n"
        f"- Ingresos totales: ${total_ingresos:,} COP\n"
        f"- Canal más rentable: {mejor_canal}\n"
    )
    return summary


def send_report(summary: str) -> str:
    """Envía el reporte por correo o lo imprime en modo demo."""
    if DEMO_MODE:
        print(summary)
        return "printed_in_demo_mode"
    if not os.getenv("SMTP_USER") or not os.getenv("SMTP_PASS"):
        raise RuntimeError("SMTP_USER and SMTP_PASS are required when DEMO_MODE=false")

    msg = EmailMessage()
    msg["Subject"] = "Reporte Semanal Automático de Ventas y Leads"
    msg["From"] = os.getenv("SMTP_USER")
    msg["To"] = os.getenv("REPORT_RECIPIENT", os.getenv("SMTP_USER", ""))
    msg.set_content(summary)

    with smtplib.SMTP(os.getenv("SMTP_HOST", "smtp.gmail.com"), int(os.getenv("SMTP_PORT", "587")), timeout=15) as server:
        server.starttls(context=ssl.create_default_context())
        server.login(os.getenv("SMTP_USER", ""), os.getenv("SMTP_PASS", ""))
        server.send_message(msg)
    return "sent"


if __name__ == "__main__":
    input_csv = Path(os.getenv("REPORT_CSV", "ventas_semana.csv"))
    if not input_csv.exists():
        if DEMO_MODE:
            create_sample_csv(input_csv)
        else:
            raise FileNotFoundError(f"Missing report input: {input_csv}")
    report_text = build_weekly_summary(input_csv)
    status = send_report(report_text)
    print(f"Estado envío: {status}")
