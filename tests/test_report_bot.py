from unittest.mock import patch
import pandas as pd
import pytest

from report_bot import build_weekly_summary, send_report


def test_build_weekly_summary_from_csv_with_currency_symbols(tmp_path):
    csv_file = tmp_path / "ventas.csv"
    csv_file.write_text(
        "fecha,canal,leads,ventas,revenue\n"
        "2026-11-20,Meta Ads,10,2,\"$2,000\"\n"
        "2026-11-21,Google Ads,10,3,\"$3,000\"\n",
        encoding="utf-8",
    )
    summary = build_weekly_summary(csv_file, currency="USD")
    assert "Total leads: 20" in summary
    assert "Total ventas: 5" in summary
    assert "Tasa de conversión: 25.0%" in summary
    assert "Ingresos totales: USD 5,000.00" in summary
    assert "Canal más rentable: Google Ads" in summary


def test_build_weekly_summary_from_excel(tmp_path):
    xlsx_file = tmp_path / "ventas.xlsx"
    pd.DataFrame(
        [
            {"canal": "Email", "leads": 8, "ventas": 4, "ingresos": 1200},
            {"canal": "Meta Ads", "leads": 2, "ventas": 0, "ingresos": 0},
        ]
    ).to_excel(xlsx_file, index=False)

    summary = build_weekly_summary(xlsx_file, currency="USD")
    assert "Total leads: 10" in summary
    assert "Canal más rentable: Email" in summary


def test_rejects_empty_file_and_missing_file(tmp_path):
    empty_csv = tmp_path / "empty.csv"
    empty_csv.write_text("canal,leads,ventas,ingresos\n", encoding="utf-8")

    with pytest.raises(ValueError, match="no contiene filas"):
        build_weekly_summary(empty_csv)
    with pytest.raises(FileNotFoundError):
        build_weekly_summary(tmp_path / "no_existe.csv")


def test_send_report(monkeypatch):
    monkeypatch.setenv("SMTP_USER", "bot@example.com")
    monkeypatch.setenv("SMTP_PASS", "app-pass")
    monkeypatch.setenv("REPORT_RECIPIENT", "gerencia@example.com")

    with patch("report_bot.smtplib.SMTP") as mock_smtp:
        status = send_report("Resumen de prueba")
    assert status == "sent"
    mock_smtp.return_value.__enter__.return_value.send_message.assert_called_once()
