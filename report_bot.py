import os
import smtplib
import ssl
from datetime import date
from email.message import EmailMessage
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

load_dotenv()


def load_sales_dataframe(
    input_path: Path, start_date: str | date | None = None, end_date: str | date | None = None
) -> pd.DataFrame:
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
        df[col] = pd.to_numeric(df[col].map(parse_numeric_value), errors="coerce").fillna(0)

    df["canal"] = df["canal"].fillna("Sin canal").astype(str).str.strip()
    if start_date is not None or end_date is not None:
        if "fecha" not in df.columns:
            raise ValueError("Se requiere la columna fecha para filtrar el periodo.")
        dates = pd.to_datetime(df["fecha"], errors="coerce").dt.date
        if start_date is not None:
            start = pd.Timestamp(start_date).date()
            df = df[dates >= start]
            dates = dates.loc[df.index]
        if end_date is not None:
            end = pd.Timestamp(end_date).date()
            df = df[dates <= end]
        if df.empty:
            raise ValueError("No hay filas dentro del periodo solicitado.")
    return df


def parse_numeric_value(value) -> float:
    """Parsea importes comunes de EE. UU. y LATAM (1,234.56 y 1.234,56)."""
    if pd.isna(value):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(" ", "").replace("'", "")
    negative_parentheses = text.startswith("(") and text.endswith(")")
    text = text.strip("()")
    text = "".join(char for char in text if char.isdigit() or char in ".,+-")
    if not text or text in {"+", "-", ".", ","}:
        return 0.0
    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        tail = text.rsplit(",", 1)[1]
        if text.count(",") == 1 and len(tail) in {1, 2} and not text.startswith("0,"):
            text = text.replace(",", ".")
        elif text.startswith("0,") and len(tail) <= 3:
            text = text.replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "." in text:
        tail = text.rsplit(".", 1)[1]
        if text.count(".") > 1:
            if len(tail) in {1, 2}:
                head, decimal = text.rsplit(".", 1)
                text = head.replace(".", "") + "." + decimal
            else:
                text = text.replace(".", "")
        elif len(tail) == 3 and not text.startswith("0."):
            text = text.replace(".", "")
    try:
        number = float(text)
    except ValueError:
        return 0.0
    return -abs(number) if negative_parentheses else number


def build_weekly_summary(
    input_path: Path,
    currency: str = "USD",
    start_date: str | date | None = None,
    end_date: str | date | None = None,
) -> str:
    """Calcula KPIs globales y desglose por canal para un periodo opcional."""
    if start_date is not None and end_date is not None and pd.Timestamp(start_date) > pd.Timestamp(end_date):
        raise ValueError("start_date no puede ser posterior a end_date.")
    df = load_sales_dataframe(input_path, start_date=start_date, end_date=end_date)

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
    report_text = build_weekly_summary(
        input_path,
        currency=currency,
        start_date=os.getenv("REPORT_START_DATE") or None,
        end_date=os.getenv("REPORT_END_DATE") or None,
    )
    status = send_report(report_text)
    print(f"Estado envío: {status}")
