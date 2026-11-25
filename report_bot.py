import os
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

load_dotenv()


def build_weekly_summary(csv_path: Path) -> str:
    """Calcula métricas clave y genera un resumen ejecutivo semanal desde un CSV real."""
    if not csv_path.exists():
        raise FileNotFoundError(f"No se encontró el archivo de entrada: {csv_path}")

    df = pd.read_csv(csv_path)
    required_cols = {"canal", "leads", "ventas", "ingresos_cop"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Faltan columnas requeridas en el CSV: {sorted(missing)}")

    total_leads = int(df["leads"].sum())
    total_ventas = int(df["ventas"].sum())
    total_ingresos = int(df["ingresos_cop"].sum())
    tasa_conv = (total_ventas / total_leads * 100) if total_leads else 0.0
    mejor_canal = df.groupby("canal")["ingresos_cop"].sum().idxmax()

    return (
        f"REPORTE SEMANAL AUTOMÁTICO\n"
        f"--------------------------\n"
        f"- Total leads: {total_leads}\n"
        f"- Total ventas: {total_ventas}\n"
        f"- Tasa de conversión: {tasa_conv:.1f}%\n"
        f"- Ingresos totales: ${total_ingresos:,} COP\n"
        f"- Canal más rentable: {mejor_canal}\n"
    )


def send_report(summary: str) -> str:
    """Envía el reporte semanal por correo vía SMTP."""
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    recipient = os.getenv("REPORT_RECIPIENT")
    if not smtp_user or not smtp_pass or not recipient:
        raise RuntimeError("SMTP_USER, SMTP_PASS y REPORT_RECIPIENT son obligatorios")

    msg = EmailMessage()
    msg["Subject"] = "Reporte Semanal Automático de Ventas y Leads"
    msg["From"] = smtp_user
    msg["To"] = recipient
    msg.set_content(summary)

    with smtplib.SMTP(os.getenv("SMTP_HOST", "smtp.gmail.com"), int(os.getenv("SMTP_PORT", "587")), timeout=15) as server:
        server.starttls(context=ssl.create_default_context())
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
    return "sent"


if __name__ == "__main__":
    input_path = Path(os.getenv("REPORT_INPUT_PATH", "ventas_semana.csv"))
    report_text = build_weekly_summary(input_path)
    status = send_report(report_text)
    print(f"Estado envío: {status}")
