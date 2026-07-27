from app.models.tennessee_oncotype import calculate_tennessee_oncotype
from app.schemas import PatientInput


def patient(**overrides):
    values = {
        "age": 55,
        "menopause": "post",
        "tumor_size_mm": 20,
        "positive_nodes": 0,
        "micrometastases": "not_applicable",
        "grade": 2,
        "histology": "idc",
        "er_percent": 90,
        "pr_percent": 70,
        "her2": "negative",
        "ki67_percent": 15,
        "vascular_invasion": "no",
        "screen_detected": "yes",
        "smoker": "no",
    }
    values.update(overrides)
    return PatientInput(**values)


def test_probabilities_are_complements():
    result = calculate_tennessee_oncotype(patient())
    assert result["available"] is True
    total = result["low_risk"]["probability"] + result["high_risk"]["probability"]
    assert abs(total - 100.0) <= 0.01


def test_manual_high_risk_formula_for_idc_grade2_pr_positive():
    result = calculate_tennessee_oncotype(patient())
    # logit = -0.003*55 + 0.02*20 + 1.097 - 3.452 = -2.120
    assert result["high_risk"]["probability"] == 10.72
    assert result["low_risk"]["probability"] == 89.28


def test_pr_negative_grade3_increases_high_risk_probability():
    low_profile = calculate_tennessee_oncotype(patient(grade=1, pr_percent=90))
    high_profile = calculate_tennessee_oncotype(patient(grade=3, pr_percent=0))
    assert high_profile["high_risk"]["probability"] > low_profile["high_risk"]["probability"]


def test_model_not_applicable_outside_published_population():
    result = calculate_tennessee_oncotype(
        patient(er_percent=0, her2="positive", positive_nodes=1, tumor_size_mm=55)
    )
    assert result["available"] is False
    assert "ER" in result["reason"]
    assert "HER2" in result["reason"]
    assert "N0" in result["reason"]
    assert "6–50" in result["reason"]
