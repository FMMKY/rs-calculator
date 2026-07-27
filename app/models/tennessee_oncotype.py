from __future__ import annotations

from math import exp

from app.schemas import PatientInput


HISTOLOGY_COEFFICIENTS = {
    "idc": 0.0,
    "ilc": -0.896,
    "idc_ilc": -0.615,
    "idc_other": -0.176,
}

HISTOLOGY_LABELS = {
    "idc": "Инвазивный протоковый рак (IDC)",
    "ilc": "Инвазивный дольковый рак (ILC)",
    "idc_ilc": "Смешанный протоковый и дольковый рак (IDC + ILC)",
    "idc_other": "Протоковый рак с другим гистологическим компонентом",
}


def _logistic(value: float) -> float:
    return 1.0 / (1.0 + exp(-value))


def _not_applicable(reason: str) -> dict:
    return {
        "available": False,
        "model": "Tennessee Oncotype DX Nomogram",
        "applicability": "не применимо",
        "reason": reason,
        "warnings": [],
    }


def calculate_tennessee_oncotype(patient: PatientInput) -> dict:
    """Predict probabilities of Oncotype DX RS 0-25 and RS 26-100.

    Formula from Orucevic et al. supplemental data. The low-risk and
    high-risk models are exact sign inverses, therefore their probabilities
    sum to 1 apart from floating-point rounding.
    """

    limitations: list[str] = []
    if patient.er_percent < 1:
        limitations.append("ER должен быть положительным (≥1%).")
    if patient.her2 != "negative":
        limitations.append("HER2 должен быть отрицательным.")
    if patient.positive_nodes != 0:
        limitations.append("Модель разработана для N0.")
    if not 6 <= patient.tumor_size_mm <= 50:
        limitations.append("Размер инвазивной опухоли должен быть 6–50 мм.")
    if not 19 <= patient.age <= 90:
        limitations.append("Возраст должен находиться в диапазоне 19–90 лет.")

    if limitations:
        return _not_applicable(" ".join(limitations))

    grade_term = {1: 0.0, 2: 1.097, 3: 2.910}[patient.grade]
    pr_negative_term = 2.032 if patient.pr_percent < 1 else 0.0
    histology_term = HISTOLOGY_COEFFICIENTS[patient.histology]

    high_logit = (
        -0.003 * patient.age
        + 0.020 * patient.tumor_size_mm
        + grade_term
        + pr_negative_term
        + histology_term
        - 3.452
    )
    high_probability = _logistic(high_logit)
    low_probability = 1.0 - high_probability

    return {
        "available": True,
        "model": "Tennessee Oncotype DX Nomogram",
        "applicability": "применима",
        "low_risk": {
            "label": "Вероятность Recurrence Score 0–25",
            "probability": round(low_probability * 100.0, 2),
        },
        "high_risk": {
            "label": "Вероятность Recurrence Score 26–100",
            "probability": round(high_probability * 100.0, 2),
        },
        "input_mapping": {
            "Возраст": f"{patient.age} лет",
            "Размер опухоли": f"{patient.tumor_size_mm:g} мм",
            "Grade": str(patient.grade),
            "PR": "отрицательный" if patient.pr_percent < 1 else "положительный",
            "Гистология": HISTOLOGY_LABELS[patient.histology],
        },
        "warnings": [
            "Номограмма прогнозирует категорию результата Oncotype DX, но не заменяет выполнение геномного теста.",
            "Индивидуальные 95% доверительные интервалы не рассчитываются: в публикации отсутствует ковариационная матрица коэффициентов, необходимая для корректного расчёта интервала конкретной пациентки.",
        ],
    }
