from unittest.mock import patch
import pytest

from report_bot import build_weekly_summary, send_report


def test_build_weekly_summary(tmp_path):
    csv_file = tmp_path / "ventas.csv"
    csv_file.write_text(
        "fecha,canal,leads,ventas,ingresos_cop\n"
        "2026-11-20,Meta Ads,10,2,2000000\n"
        "2026-11-21,Google Ads,10,3,3000000\n",
        encoding="utf-8",
    )
    summary = build_weekly_summary(csv_file)
    assert "Total leads: 20" in summary
    assert "Total ventas: 5" in summary
    assert "Tasa de conversión: 25.0%" in summary
    assert "Canal más rentable: Google Ads" in summary


def test_build_weekly_summary_missing_file(tmp_path):
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
