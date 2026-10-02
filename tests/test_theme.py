from aegislog.theme import risk_style, severity_style


def test_severity_colors_keep_distinct_semantics():
    assert severity_style("CRITICAL") == "bold #FF3030"
    assert severity_style("HIGH") == "#FF6268"
    assert severity_style("MEDIUM") == "#FF981F"
    assert severity_style("LOW") == "#22C5DA"
    assert severity_style("INFO") == "#A6A6A6"


def test_risk_colors_cover_clear_review_and_alert_states():
    assert risk_style("CLEAR") == "#64FFDA"
    assert risk_style("REVIEW") == "#FF981F"
    assert risk_style("HIGH") == "#FF6268"
    assert risk_style("CRITICAL") == "bold #FF3030"
