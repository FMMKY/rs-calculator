from __future__ import annotations

from app.models.crib_common import Contribution, result_payload
from app.schemas import PatientInput


POSTMENOPAUSAL_DFS_TABLE = [
    {
        "risk_code": "low",
        "risk_label": "Низкий риск",
        "parameter_estimate": "<0,66",
        "letrozole": 96,
        "letrozole_to_tamoxifen": 94,
        "tamoxifen_to_letrozole": 93,
        "tamoxifen": 94,
    },
    {
        "risk_code": "intermediate",
        "risk_label": "Промежуточный (умеренный) риск",
        "parameter_estimate": "0,66–1,53",
        "letrozole": 90,
        "letrozole_to_tamoxifen": 91,
        "tamoxifen_to_letrozole": 93,
        "tamoxifen": 86,
    },
    {
        "risk_code": "high",
        "risk_label": "Высокий риск",
        "parameter_estimate": ">1,53",
        "letrozole": 80,
        "letrozole_to_tamoxifen": 76,
        "tamoxifen_to_letrozole": 74,
        "tamoxifen": 69,
    },
]

TREATMENT_LABELS = {
    "letrozole": "Летрозол",
    "letrozole_to_tamoxifen": "Летрозол → тамоксифен",
    "tamoxifen_to_letrozole": "Тамоксифен → летрозол",
    "tamoxifen": "Тамоксифен",
}


def _age(age: int) -> tuple[str, float]:
    if age < 55:
        return "<55 лет", 0.00
    if age <= 69:
        return "55–69 лет", 0.24
    return "≥70 лет", 0.72


def _nodes(nodes: int) -> tuple[str, float]:
    if nodes == 0:
        return "0", 0.00
    if nodes <= 3:
        return "1–3", 0.46
    if nodes <= 9:
        return "4–9", 0.71
    return "≥10", 1.50


def _size(size_mm: float) -> tuple[str, float]:
    if size_mm <= 20:
        return "≤2 см", 0.00
    if size_mm < 50:
        return ">2–<5 см", 0.30
    return "≥5 см", 0.56


def _grade(grade: int) -> tuple[str, float]:
    return {
        1: ("Grade 1", 0.00),
        2: ("Grade 2", 0.26),
        3: ("Grade 3", 0.53),
    }[grade]


def _ki67(value: float) -> tuple[str, float]:
    if value < 14:
        return "<14%", 0.00
    if value < 34:
        return "14–33%", 0.26
    return "≥34%", 0.50


def _er(value: float) -> tuple[str, float]:
    if value < 30:
        return "<30%", 0.48
    if value < 50:
        return "30–49%", 0.20
    return "≥50%", 0.00


def _her2(value: str) -> tuple[str, float]:
    if value == "positive":
        return "Положительный", 0.36
    if value == "negative":
        return "Отрицательный", 0.00
    raise ValueError(
        "Для постменопаузального CRIB требуется известный HER2-статус."
    )


def _pr(value: float) -> tuple[str, float]:
    if value < 20:
        return "<20%", 0.22
    if value < 70:
        return "20–69%", 0.08
    return "≥70%", 0.00


def _vascular(value: str) -> tuple[str, float]:
    if value == "yes":
        return "Есть", 0.17
    if value == "no":
        return "Нет", 0.00
    raise ValueError(
        "Для постменопаузального CRIB требуется известный статус сосудистой инвазии."
    )


def _risk_interpretation(score: float) -> tuple[str, str, str]:
    if score < 0.66:
        return (
            "low",
            "Низкий риск",
            "Ниже 25-го перцентиля исходной выборки (<0,66)",
        )
    if score <= 1.53:
        return (
            "intermediate",
            "Промежуточный (умеренный) риск",
            "Межквартильный диапазон исходной выборки (0,66–1,53)",
        )
    return (
        "high",
        "Высокий риск",
        "Выше 75-го перцентиля исходной выборки (>1,53)",
    )


def _dfs_payload(risk_code: str) -> dict:
    active_row = next(
        row for row in POSTMENOPAUSAL_DFS_TABLE
        if row["risk_code"] == risk_code
    )
    treatment_keys = list(TREATMENT_LABELS)
    best_value = max(active_row[key] for key in treatment_keys)
    best_strategies = [
        TREATMENT_LABELS[key]
        for key in treatment_keys
        if active_row[key] == best_value
    ]
    return {
        "title": "5-летняя выживаемость без признаков заболевания (DFS)",
        "rows": POSTMENOPAUSAL_DFS_TABLE,
        "active_risk_code": risk_code,
        "best_observed_value": best_value,
        "best_observed_strategies": best_strategies,
        "interpretation": (
            "Наибольшая наблюдаемая 5-летняя DFS в этой группе риска: "
            f"{', '.join(best_strategies)} — {best_value}%."
        ),
        "caution": (
            "Это групповые оценки из поданализа BIG 1-98, а не "
            "индивидуальная вероятность ответа на терапию и не автоматическая "
            "рекомендация по выбору препарата."
        ),
    }


def calculate_crib_post(patient: PatientInput) -> dict:
    categories = [
        ("Положительные лимфоузлы", _nodes(patient.positive_nodes)),
        ("Возраст", _age(patient.age)),
        ("Размер опухоли", _size(patient.tumor_size_mm)),
        ("Степень злокачественности", _grade(patient.grade)),
        ("Ki-67", _ki67(patient.ki67_percent)),
        ("ER", _er(patient.er_percent)),
        ("HER2", _her2(patient.her2)),
        ("PgR", _pr(patient.pr_percent)),
        ("Перитуморальная сосудистая инвазия", _vascular(patient.vascular_invasion)),
    ]
    contributions = [
        Contribution(factor=name, category=category, coefficient=coefficient)
        for name, (category, coefficient) in categories
    ]
    score = sum(item.coefficient for item in contributions)
    risk_code, risk_label, risk_band = _risk_interpretation(score)

    warnings: list[str] = []
    if patient.er_percent <= 0:
        warnings.append("BIG 1-98 включал опухоли с подтвержденной экспрессией ER.")
    if patient.menopause != "post":
        warnings.append("Выбрана не постменопауза.")

    applicability = "применима" if not warnings else "ограниченная применимость"

    return result_payload(
        model="CRIB postmenopausal — BIG 1-98",
        score=score,
        contributions=contributions,
        applicability=applicability,
        warnings=warnings,
        risk_band=risk_band,
        endpoint="Composite prognostic risk для 5-летней DFS в анализе BIG 1-98",
        extra={
            "risk_code": risk_code,
            "risk_label": risk_label,
            "postmenopausal_dfs": _dfs_payload(risk_code),
        },
    )
