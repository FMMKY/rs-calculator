from app.models.crib_post import calculate_crib_post
from app.models.crib_pre import calculate_crib_pre
from app.schemas import PatientInput


def patient(**overrides):
    values = {
        "age": 55,
        "menopause": "post",
        "tumor_size_mm": 20,
        "positive_nodes": 0,
        "micrometastases": "not_applicable",
        "grade": 2,
        "er_percent": 90,
        "pr_percent": 70,
        "her2": "negative",
        "ki67_percent": 15,
        "vascular_invasion": "no",
        "screen_detected": "no",
        "smoker": "no",
    }
    values.update(overrides)
    return PatientInput(**values)


def test_postmenopausal_published_example_is_1_22():
    case = patient(age=60, positive_nodes=2, grade=2, er_percent=90, pr_percent=80, her2="negative", ki67_percent=20, vascular_invasion="no")
    assert calculate_crib_post(case)["score"] == 1.22


def test_premenopausal_reference_profile_is_zero():
    case = patient(age=47, menopause="pre", grade=1, er_percent=90, pr_percent=80, her2="negative", ki67_percent=10)
    assert calculate_crib_pre(case)["score"] == 0.0


def test_premenopausal_high_profile():
    case = patient(age=34, menopause="pre", tumor_size_mm=25, positive_nodes=4, grade=2, er_percent=40, pr_percent=10, her2="negative", ki67_percent=27)
    assert calculate_crib_pre(case)["score"] == 4.61


def test_postmenopausal_risk_groups_and_best_observed_strategy():
    low = calculate_crib_post(patient(age=50, grade=1, ki67_percent=10))
    intermediate = calculate_crib_post(patient(positive_nodes=1, grade=1, ki67_percent=40))
    high = calculate_crib_post(patient(age=72, positive_nodes=10, tumor_size_mm=55, grade=3, er_percent=20, pr_percent=10, her2="positive", ki67_percent=40, vascular_invasion="yes"))
    assert low["risk_code"] == "low"
    assert intermediate["score"] == 1.20
    assert intermediate["risk_code"] == "intermediate"
    assert high["risk_code"] == "high"


def test_postmenopausal_dfs_table_matches_original_crib_values():
    result = calculate_crib_post(patient())
    rows = {row["risk_code"]: row for row in result["postmenopausal_dfs"]["rows"]}
    assert [rows["low"]["letrozole"], rows["low"]["letrozole_to_tamoxifen"], rows["low"]["tamoxifen_to_letrozole"], rows["low"]["tamoxifen"]] == [96, 94, 93, 94]
    assert [rows["intermediate"]["letrozole"], rows["intermediate"]["letrozole_to_tamoxifen"], rows["intermediate"]["tamoxifen_to_letrozole"], rows["intermediate"]["tamoxifen"]] == [90, 91, 93, 86]
    assert [rows["high"]["letrozole"], rows["high"]["letrozole_to_tamoxifen"], rows["high"]["tamoxifen_to_letrozole"], rows["high"]["tamoxifen"]] == [80, 76, 74, 69]
