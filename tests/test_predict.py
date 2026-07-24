from app.models.predict_v3 import TreatmentScenario, calculate_predict, calculate_survival
from app.schemas import PatientInput


def patient(**overrides):
    values = {"age":55,"menopause":"post","tumor_size_mm":20,"positive_nodes":0,"micrometastases":"not_applicable","grade":2,"er_percent":90,"pr_percent":70,"her2":"negative","ki67_percent":15,"vascular_invasion":"no","screen_detected":"yes","smoker":"no","endocrine_therapy":"none"}
    values.update(overrides)
    return PatientInput(**values)


def test_survival_is_bounded():
    result = calculate_survival(patient(), TreatmentScenario())
    assert all(0 <= value <= 100 for value in result.values())


def test_first_official_screenshot_matches_exact_v32_output():
    case = patient(age=30, menopause="pre", tumor_size_mm=30, positive_nodes=4, grade=2, er_percent=90, pr_percent=0, her2="negative", ki67_percent=90, screen_detected="yes", endocrine_therapy="five", chemotherapy="third", prior_chemotherapy="yes")
    rows = calculate_predict(case)["horizons"][0]["rows"]
    assert rows[0]["survival_exact"] == 85.97
    assert rows[0]["survival_display"] == 86
    assert rows[1]["additional_benefit"] == 4.2
    assert rows[2]["additional_benefit"] == 3.3


def test_second_official_screenshot_matches_exact_v32_output():
    case = patient(age=55, menopause="post", tumor_size_mm=15, positive_nodes=1, micrometastases="no", grade=1, er_percent=90, pr_percent=90, her2="negative", ki67_percent=90, screen_detected="yes", radiotherapy=True, heart_dose_gy=0, endocrine_therapy="five", bisphosphonates=True)
    rows = calculate_predict(case)["horizons"][0]["rows"]
    assert rows[0]["survival_exact"] == 97.80
    assert rows[1]["additional_benefit"] == 0.2
    assert rows[2]["additional_benefit"] == 0.4
    assert rows[3]["additional_benefit"] == 0.1


def test_micrometastases_map_one_node_to_point_five():
    full_result = calculate_survival(patient(positive_nodes=1, micrometastases="no"), TreatmentScenario())
    micro_result = calculate_survival(patient(positive_nodes=1, micrometastases="yes"), TreatmentScenario())
    assert micro_result[10] > full_result[10]


def test_ten_year_hormone_matches_five_years_until_year_ten():
    case = patient()
    five = calculate_survival(case, TreatmentScenario(endocrine_duration="five"))
    ten = calculate_survival(case, TreatmentScenario(endocrine_duration="ten"))
    assert five[5] == ten[5]
    assert five[10] == ten[10]
    assert ten[15] > five[15]
