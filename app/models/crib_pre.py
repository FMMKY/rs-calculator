from __future__ import annotations

from app.models.crib_common import Contribution, result_payload
from app.schemas import PatientInput


def _age(age: int) -> tuple[str, float]:
    if age < 35:
        return "<35 лет", 0.77
    if age <= 39:
        return "35–39 лет", 0.62
    if age <= 44:
        return "40–44 года", 0.17
    if age <= 49:
        return "45–49 лет", 0.00
    return "≥50 лет", 0.06


def _nodes(nodes: int) -> tuple[str, float]:
    if nodes == 0:
        return "0", 0.00
    if nodes <= 3:
        return "1–3", 0.54
    return "≥4", 1.38


def _size(size_mm: float) -> tuple[str, float]:
    if size_mm <= 20:
        return "≤2 см", 0.00
    return ">2 см", 0.58


def _grade(grade: int) -> tuple[str, float]:
    return {
        1: ("Grade 1", 0.00),
        2: ("Grade 2", 0.81),
        3: ("Grade 3", 0.78),
    }[grade]


def _er(value: float) -> tuple[str, float]:
    if value < 50:
        return "<50%", 0.14
    return "≥50%", 0.00


def _pr(value: float) -> tuple[str, float]:
    if value < 20:
        return "<20%", 0.44
    if value < 50:
        return "20–49%", 0.29
    return "≥50%", 0.00


def _ki67(value: float) -> tuple[str, float]:
    if value < 14:
        return "<14%", 0.00
    if value < 20:
        return "14–19%", -0.10
    if value < 26:
        return "20–25%", 0.26
    return "≥26%", 0.49


def calculate_crib_pre(patient: PatientInput) -> dict:
    categories = [
        ("Возраст", _age(patient.age)),
        ("Положительные лимфоузлы", _nodes(patient.positive_nodes)),
        ("Размер опухоли", _size(patient.tumor_size_mm)),
        ("Степень злокачественности", _grade(patient.grade)),
        ("ER", _er(patient.er_percent)),
        ("PgR", _pr(patient.pr_percent)),
        ("Ki-67", _ki67(patient.ki67_percent)),
    ]
    contributions = [
        Contribution(factor=name, category=category, coefficient=coefficient)
        for name, (category, coefficient) in categories
    ]
    score = sum(item.coefficient for item in contributions)

    warnings: list[str] = []
    hr_positive = patient.er_percent >= 10 or patient.pr_percent >= 10
    if not hr_positive:
        warnings.append(
            "TEXT/SOFT включали гормонорецептор-положительные опухоли; "
            "введенные ER/PgR не соответствуют этой популяции."
        )
    if patient.her2 != "negative":
        warnings.append(
            "Пременопаузальная модель была построена для HER2-негативной популяции."
        )
    if patient.menopause != "pre":
        warnings.append("Выбрана не пременопауза.")

    applicability = "применима" if not warnings else "ограниченная применимость"
    cohort = (
        "TEXT/SOFT: с предшествующей химиотерапией"
        if patient.prior_chemotherapy == "yes"
        else "TEXT/SOFT: без предшествующей химиотерапии"
    )

    return result_payload(
        model="CRIB premenopausal — TEXT/SOFT, DRFI model",
        score=score,
        contributions=contributions,
        applicability=applicability,
        warnings=warnings,
        risk_band=None,
        endpoint="Непрерывный composite risk для анализа 8-летней свободы от отдаленного рецидива",
        extra={"interpretation_cohort": cohort},
    )
