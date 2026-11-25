import pytest

import report_bot


def test_production_missing_smtp_is_error(monkeypatch):
    monkeypatch.setattr(report_bot, "DEMO_MODE", False)
    monkeypatch.delenv("SMTP_USER", raising=False)
    monkeypatch.delenv("SMTP_PASS", raising=False)
    with pytest.raises(RuntimeError, match="SMTP_USER and SMTP_PASS"):
        report_bot.send_report("example")


def test_summary_uses_supplied_csv(tmp_path):
    path = tmp_path / "ventas.csv"
    path.write_text("fecha,canal,leads,ventas,ingresos_cop\n2026-11-24,Web,10,2,100000\n", encoding="utf-8")
    summary = report_bot.build_weekly_summary(path)
    assert "Total leads: 10" in summary
    assert "Tasa de conversión: 20.0%" in summary
    assert "Web" in summary
