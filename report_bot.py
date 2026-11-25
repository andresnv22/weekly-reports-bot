import os
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

load_dotenv()


def load_sales_dataframe(input_path: Path) -> pd.DataFrame:
    """Carga datos desde CSV o Excel (.xlsx/.xls) y valida esquema."""
    if not input_path.exists():
        raise FileNotFoundError(f"No se encontró el archivo de entrada: {input_path}")

    suffix = input_path.suffix.lower()
    if suffix == ".csv":
        df = pd.read_csv(input_path)
    elif suffix in {".xlsx", ".xls"}:
        df = pd.read_excel(input_path)
    else:
        raise ValueError(f"Formato no soportado ({suffix}). Usa .csv o .xlsx")

    if df.empty:
        raise ValueError("El archivo de entrada no contiene filas.")

    # Acepta 'ingresos' o 'ingresos_cop' o 'revenue'
    if "ingresos" not in df.columns:
        if "ingresos_cop" in df.columns:
            df = df.rename(columns={"ingresos_cop": "ingresos"})
        elif "revenue" in df.columns:
            df = df.rename(columns={"revenue": "ingresos"})

    required_cols = {"canal", "leads", "ventas", "ingresos"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Faltan columnas requeridas: {sorted(missing)}")

    for col in ("leads", "ventas", "ingresos"):
        cleaned = (
            df[col]
            .astype(str)
            .str.replace(r"[^0-9.\-]", "", regex=True)
            .replace("", "0")
        )
        df[col] = pd.to_numeric(cleaned, errors="coerce").fillna(0)

    df["canal"] = df["canal"].fillna("Sin canal").astype(str).str.strip()
    return df


def build_weekly_summary(input_path: Path, currency: str = "USD") -> str:
    """Calcula KPIs globales y desglose por canal."""
    df = load_sales_dataframe(input_path)

    total_leads = int(df["leads"].sum())
    total_ventas = int(df["ventas"].sum())
    total_ingresos = float(df["ingresos"].sum())
    tasa_conv = (total_ventas / total_leads * 100) if total_leads else 0.0

    by_channel = (
        df.groupby("canal", as_index=True)[["leads", "ventas", "ingresos"]]
        .sum()
        .sort_values("ingresos", ascending=False)
    )
    mejor_canal = str(by_channel.index[0])

    lines = [
        "REPORTE SEMANAL AUTOMÁTICO",
        "--------------------------",
        f"- Total leads: {total_leads}",
        f"- Total ventas: {total_ventas}",
        f"- Tasa de conversión: {tasa_conv:.1f}%",
        f"- Ingresos totales: {currency} {total_ingresos:,.2f}",
        f"- Canal más rentable: {mejor_canal}",
        "",
        "Desglose por canal:",
    ]
    for canal, row in by_channel.iterrows():
        lines.append(
            f"  * {canal}: {int(row['leads'])} leads | {int(row['ventas'])} ventas | {currency} {row['ingresos']:,.2f}"
        )
    return "\n".join(lines) + "\n"


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

    with smtplib.SMTP(
        os.getenv("SMTP_HOST", "smtp.gmail.com"),
        int(os.getenv("SMTP_PORT", "587")),
        timeout=15,
    ) as server:
        server.starttls(context=ssl.create_default_context())
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
    return "sent"


if __name__ == "__main__":
    input_path = Path(os.getenv("REPORT_INPUT_PATH", "ventas_semana.csv"))
    currency = os.getenv("CURRENCY", "USD")
    report_text = build_weekly_summary(input_path, currency=currency)
    status = send_report(report_text)
    print(f"Estado envío: {status}")
