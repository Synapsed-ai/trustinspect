from dataclasses import dataclass, field

from trustinspect.reporting.aitg_visuals import build_aitg_visual_summary


@dataclass
class Obs:
    test_id: str
    classification: str


@dataclass
class Assessment:
    observations: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


def test_aitg_visual_summary_uses_official_layers_only():
    assessment = Assessment(
        observations=[
            Obs("AITG-APP-01", "SAFE"),
            Obs("AITG-APP-03-DYN-001", "VULNERABILITY"),
            Obs("AITG-MOD-01", "ERROR"),
            Obs("AITG-INF-02", "POSSIBLE VULNERABILITY"),
            Obs("AITG-DAT-05", "SAFE"),
        ]
    )
    summary = build_aitg_visual_summary(assessment)
    assert summary["is_aitg"] is True
    layer_names = [row["layer"] for row in summary["layers"]]
    assert layer_names == [
        "AI Application Testing",
        "AI Model Testing",
        "AI Infrastructure Testing",
        "AI Data Testing",
    ]
    assert all("Privacy" not in row["layer"] for row in summary["layers"])
    assert summary["totals"]["vulnerabilities"] == 1
    assert summary["totals"]["errors"] == 1
