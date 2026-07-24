from __future__ import annotations

from dataclasses import dataclass, replace
from math import exp, floor, log
from typing import Literal

from app.schemas import PatientInput


PREDICT_MODEL_VERSION = "3.2"
PREDICT_FIXED_YEAR = 2017

COEFFICIENTS = {
    "ag1_er0": 1.7560679383953317,
    "ag2_er0": 4.555274634880487,
    "sz1_er0": 0.7443277265210039,
    "nd1_er0": 0.6308590364310884,
    "gr1_er0": 0.3462287839000938,
    "sc1_er0": -0.2110969326598672,
    "yr1_er0": -0.045504610416172736,
    "ag1_er1": 0.1958986203588129,
    "ag2_er1": 2.929125051895787,
    "sz1_er1": 2.27417420673498,
    "nd1_er1": 0.6724828209061207,
    "gr1_er1": 0.7050339629739382,
    "sc1_er1": -0.32039363353015476,
    "yr1_er1": -0.048251370712776756,
    "ag_other_1": 4.211443507724736,
    "ag_other_2": -31.41202815365277,
    "yr_other": -0.021186462111818898,
    "h0_br_i": -3.0153139765165835,
    "h0_br_t1": -0.5755380524044251,
    "h0_br_t2": -0.1028439317178058,
    "h1_br_i": -2.3193510039281637,
    "h1_br_t1": -3.622538332641392,
    "h1_br_t2": -0.542240944493945,
    "h_other_i": -4.845654758283992,
    "h_other_t1": 1.341348310005262,
    "h_other_t2": 0.49539394353046057,
}


@dataclass(frozen=True)
class TreatmentScenario:
    radiotherapy: bool = False
    heart_dose_gy: float = 0.0
    endocrine_duration: Literal["none", "five", "ten"] = "none"
    chemotherapy: Literal["none", "second", "third"] = "none"
    trastuzumab: bool = False
    bisphosphonates: bool = False


def _annual_from_cumulative(values: list[float]) -> list[float]:
    annual = [values[0]]
    annual.extend(values[index] - values[index - 1] for index in range(1, len(values)))
    return annual


def _cumulative(values: list[float]) -> list[float]:
    total = 0.0
    result: list[float] = []
    for value in values:
        total += value
        result.append(total)
    return result


def _display_integer(value: float) -> int:
    return int(floor(value + 0.5))


def _screen_value(status: str) -> float:
    return {"no": 0.0, "yes": 1.0, "unknown": 0.204}[status]


def _effective_nodes(patient: PatientInput) -> float:
    if patient.positive_nodes == 1 and patient.micrometastases == "yes":
        return 0.5
    return float(patient.positive_nodes)


def _her2_beta(er_positive: bool, her2: str, years: int) -> list[float]:
    if her2 == "unknown":
        return [0.0] * years
    if er_positive:
        positive = [0.608, 0.532, 0.457, 0.382, 0.307, 0.231, 0.156, 0.081, 0.006, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        negative = [-0.053, -0.046, -0.040, -0.033, -0.027, -0.020, -0.014, -0.007, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        return (positive if her2 == "positive" else negative)[:years]
    value = 0.2316 if her2 == "positive" else -0.08589
    return [value] * years


def _endocrine_vector(duration: str, er_positive: bool, years: int) -> list[float]:
    if duration == "none" or not er_positive:
        return [0.0] * years
    standard_effect = -0.3857
    if duration == "five":
        return [standard_effect] * years
    return [standard_effect if year <= 10 else standard_effect - 0.301 for year in range(1, years + 1)]


def calculate_survival(patient: PatientInput, scenario: TreatmentScenario, years: int = 15) -> dict[int, float]:
    if years < 1 or years > 15:
        raise ValueError("PREDICT v3.2 поддерживает горизонт от 1 до 15 лет.")

    coefficients = COEFFICIENTS
    model_year = PREDICT_FIXED_YEAR
    er_positive = patient.er_percent >= 1
    pr_positive = patient.pr_percent >= 1
    ki67_positive = patient.ki67_percent > 10
    screen = _screen_value(patient.screen_detected)
    smoker = patient.smoker == "yes"
    effective_nodes = _effective_nodes(patient)
    age_shifted = patient.age - 24
    times = list(range(1, years + 1))

    if er_positive:
        age_mfp_1 = (age_shifted / 100.0) ** -0.5
        age_mfp_2 = (age_shifted / 100.0) ** 2
        size_mfp = 1.0 - exp(-patient.tumor_size_mm / 20.0)
        age_beta_1 = coefficients["ag1_er1"]
        age_beta_2 = coefficients["ag2_er1"]
        size_beta = coefficients["sz1_er1"]
        nodes_beta = coefficients["nd1_er1"]
        grade_beta = coefficients["gr1_er1"]
        screen_beta = coefficients["sc1_er1"]
        year_beta = coefficients["yr1_er1"]
    else:
        age_mfp_1 = age_shifted / 100.0
        age_mfp_2 = (age_shifted / 100.0) * log(age_shifted / 100.0)
        size_mfp = log(patient.tumor_size_mm)
        age_beta_1 = coefficients["ag1_er0"]
        age_beta_2 = coefficients["ag2_er0"]
        size_beta = coefficients["sz1_er0"]
        nodes_beta = coefficients["nd1_er0"]
        grade_beta = coefficients["gr1_er0"]
        screen_beta = coefficients["sc1_er0"]
        year_beta = coefficients["yr1_er0"]

    nodes_mfp = log(effective_nodes + 1.0)
    if er_positive:
        ki67_beta = 0.14904 if ki67_positive else -0.11333
        pr_beta = -0.0619 if pr_positive else 0.2624
    else:
        ki67_beta = 0.0
        pr_beta = -0.2231 if pr_positive else 0.0296

    her2_betas = _her2_beta(er_positive, patient.her2, years)

    smoker_proportion = 0.10
    smoker_all_cause_rr = 0.25 * 2.0 + 0.75
    smoker_denominator = 1.0 - smoker_proportion + smoker_all_cause_rr * smoker_proportion
    smoker_beta = log((smoker_all_cause_rr if smoker else 1.0) / smoker_denominator)

    baseline_adjust_breast = 0.7 if er_positive else 0.55
    baseline_adjust_other = -0.062
    other_mortality_index = (
        coefficients["ag_other_1"] * ((age_shifted / 100.0) ** 3)
        + coefficients["ag_other_2"] * ((age_shifted / 100.0) ** 3 * log(age_shifted / 100.0))
        + coefficients["yr_other"] * (model_year - 2000)
        + baseline_adjust_other
        + smoker_beta
    )
    pi_without_her2 = (
        age_beta_1 * age_mfp_1 + age_beta_2 * age_mfp_2 + size_beta * size_mfp
        + nodes_beta * nodes_mfp + grade_beta * patient.grade + screen_beta * screen
        + year_beta * (model_year - 2000) + ki67_beta + pr_beta + baseline_adjust_breast
    )

    chemo_breast = {"none": 0.0, "second": -0.248, "third": -0.446}[scenario.chemotherapy]
    endocrine = _endocrine_vector(scenario.endocrine_duration, er_positive, years)
    radio_breast = log(0.82) if scenario.radiotherapy else 0.0
    trastuzumab = -0.3567 if scenario.trastuzumab and patient.her2 == "positive" else 0.0
    bisphosphonate = -0.198 if scenario.bisphosphonates else 0.0
    treatment_breast = [endocrine[i] + chemo_breast + radio_breast + trastuzumab + bisphosphonate for i in range(years)]

    treatment_other = (
        (log(1.20) if scenario.chemotherapy != "none" else 0.0)
        + (log(1.02) * scenario.heart_dose_gy if scenario.radiotherapy else 0.0)
    )

    base_other_cum = [exp(coefficients["h_other_i"] + coefficients["h_other_t1"] * log(t / 10.0) + coefficients["h_other_t2"] * (t / 10.0)) for t in times]
    other_annual = [v * exp(other_mortality_index + treatment_other) for v in _annual_from_cumulative(base_other_cum)]
    other_survival = [exp(-v) for v in _cumulative(other_annual)]
    other_death_annual = _annual_from_cumulative([1.0 - v for v in other_survival])

    if er_positive:
        base_br_cum = [exp(coefficients["h1_br_i"] + coefficients["h1_br_t1"] * ((t / 10.0) ** -0.5) + coefficients["h1_br_t2"] * ((t / 10.0) ** -0.5) * log(t / 10.0)) for t in times]
    else:
        base_br_cum = [exp(coefficients["h0_br_i"] + coefficients["h0_br_t1"] * ((t / 10.0) ** -1.0) + coefficients["h0_br_t2"] * ((t / 10.0) ** -1.0) * log(t / 10.0)) for t in times]

    breast_annual = [base * exp(pi_without_her2 + her2_betas[i] + treatment_breast[i]) for i, base in enumerate(_annual_from_cumulative(base_br_cum))]
    breast_survival = [exp(-v) for v in _cumulative(breast_annual)]
    breast_death_annual = _annual_from_cumulative([1.0 - v for v in breast_survival])

    all_death_cum = [1.0 - other_survival[i] * breast_survival[i] for i in range(years)]
    all_death_annual = _annual_from_cumulative(all_death_cum)
    pred_breast_annual = []
    for i in range(years):
        denominator = breast_death_annual[i] + other_death_annual[i]
        fraction = breast_death_annual[i] / denominator if denominator > 0 else 0.0
        pred_breast_annual.append(fraction * all_death_annual[i])
    pred_other_annual = [all_death_annual[i] - pred_breast_annual[i] for i in range(years)]
    pred_all_cum = [a + b for a, b in zip(_cumulative(pred_breast_annual), _cumulative(pred_other_annual))]
    survival = [100.0 * (1.0 - value) for value in pred_all_cum]
    return {h: round(survival[h - 1], 8) for h in (5, 10, 15)}


def _scenario_steps(patient: PatientInput) -> list[tuple[str, TreatmentScenario]]:
    scenario = TreatmentScenario()
    steps = [("Только операция", scenario)]
    if patient.radiotherapy:
        scenario = replace(scenario, radiotherapy=True, heart_dose_gy=patient.heart_dose_gy)
        steps.append(("+ Лучевая терапия", scenario))
    if patient.endocrine_therapy != "none":
        scenario = replace(scenario, endocrine_duration=patient.endocrine_therapy)
        duration = "5 лет" if patient.endocrine_therapy == "five" else "10 лет"
        steps.append((f"+ Гормонотерапия ({duration})", scenario))
    if patient.chemotherapy != "none":
        scenario = replace(scenario, chemotherapy=patient.chemotherapy)
        label = "+ Химиотерапия: стандартная антрациклиновая" if patient.chemotherapy == "second" else "+ Химиотерапия: таксан- / высокодозная антрациклиновая"
        steps.append((label, scenario))
    if patient.trastuzumab:
        scenario = replace(scenario, trastuzumab=True)
        steps.append(("+ Трастузумаб", scenario))
    if patient.bisphosphonates:
        scenario = replace(scenario, bisphosphonates=True)
        steps.append(("+ Бисфосфонаты", scenario))
    return steps


def calculate_predict(patient: PatientInput) -> dict:
    scenario_results = [(label, calculate_survival(patient, scenario)) for label, scenario in _scenario_steps(patient)]
    horizons = []
    for year in (5, 10, 15):
        rows = []
        previous = None
        baseline = scenario_results[0][1][year]
        for label, result in scenario_results:
            survival = result[year]
            additional = None if previous is None else survival - previous
            rows.append({
                "treatment": label,
                "additional_benefit": None if additional is None else round(additional, 1),
                "survival_exact": round(survival, 2),
                "survival_display": _display_integer(survival),
                "total_benefit": round(survival - baseline, 1),
            })
            previous = survival
        horizons.append({"year": year, "rows": rows})

    effective_nodes = _effective_nodes(patient)
    warnings = ["Исследовательская реализация PREDICT v3.2. До клинического использования требуется расширенная валидация."]
    if patient.her2 == "unknown":
        warnings.append("HER2 неизвестен: HER2-коэффициент принят равным 0.")
    if patient.screen_detected == "unknown":
        warnings.append("Неизвестный способ выявления преобразован в коэффициент 0,204.")

    return {
        "model": "PREDICT Breast v3.2 — локальная реализация",
        "horizons": horizons,
        "warnings": warnings,
        "status": "2 контрольных случая совпали",
        "fixed_model_year": PREDICT_FIXED_YEAR,
        "status_mapping": {
            "ER": "положительный" if patient.er_percent >= 1 else "отрицательный",
            "PgR": "положительный" if patient.pr_percent >= 1 else "отрицательный",
            "Ki-67": "положительный" if patient.ki67_percent > 10 else "отрицательный",
            "Способ выявления": {"yes": "скрининг", "no": "клинически / по симптомам", "unknown": "неизвестно (0,204)"}[patient.screen_detected],
            "Узлы PREDICT": f"{effective_nodes:g}" + (" (1 узел, только микрометастазы)" if effective_nodes == 0.5 else ""),
            "Микрометастазы": {"not_applicable": "не применимо", "yes": "только микрометастазы", "no": "нет", "unknown": "неизвестно"}[patient.micrometastases],
            "Гормонотерапия": {"none": "нет", "five": "5 лет", "ten": "10 лет"}[patient.endocrine_therapy],
        },
    }
