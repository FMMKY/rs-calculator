from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Contribution:
    factor: str
    category: str
    coefficient: float

    def to_dict(self) -> dict:
        return asdict(self)


def result_payload(
    *,
    model: str,
    score: float,
    contributions: list[Contribution],
    applicability: str,
    warnings: list[str],
    risk_band: str | None = None,
    endpoint: str,
    extra: dict | None = None,
) -> dict:
    result = {
        "model": model,
        "score": round(score, 4),
        "risk_band": risk_band,
        "endpoint": endpoint,
        "applicability": applicability,
        "warnings": warnings,
        "contributions": [item.to_dict() for item in contributions],
    }
    if extra:
        result.update(extra)
    return result
