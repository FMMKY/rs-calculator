from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class PatientInput(BaseModel):
    age: int = Field(ge=25, le=85)
    menopause: Literal["pre", "post"]
    tumor_size_mm: float = Field(gt=0, le=500)
    positive_nodes: int = Field(ge=0, le=100)
    micrometastases: Literal["not_applicable", "yes", "no", "unknown"] = "not_applicable"
    grade: Literal[1, 2, 3]
    histology: Literal["idc", "ilc", "idc_ilc", "idc_other"] = "idc"
    er_percent: float = Field(ge=0, le=100)
    pr_percent: float = Field(ge=0, le=100)
    her2: Literal["negative", "positive", "unknown"]
    ki67_percent: float = Field(ge=0, le=100)
    vascular_invasion: Literal["no", "yes", "unknown"]
    screen_detected: Literal["no", "yes", "unknown"] = "no"
    smoker: Literal["no", "yes"] = "no"
    distant_metastasis: bool = False
    radiotherapy: bool = False
    heart_dose_gy: float = Field(default=0, ge=0, le=20)
    endocrine_therapy: Literal["none", "five", "ten"] = "none"
    chemotherapy: Literal["none", "second", "third"] = "none"
    trastuzumab: bool = False
    bisphosphonates: bool = False
    prior_chemotherapy: Literal["yes", "no"] = "no"

    @model_validator(mode="after")
    def validate_logic(self) -> "PatientInput":
        if self.distant_metastasis:
            raise ValueError("PREDICT предназначен для раннего неметастатического рака молочной железы.")
        if not self.radiotherapy and self.heart_dose_gy != 0:
            raise ValueError("Средняя доза на сердце должна быть 0, если лучевая терапия не выбрана.")
        if self.positive_nodes != 1 and self.micrometastases != "not_applicable":
            raise ValueError("Параметр «только микрометастазы» применяется только при одном положительном лимфоузле.")
        if self.endocrine_therapy != "none" and self.er_percent < 1:
            raise ValueError("Гормонотерапия в PREDICT доступна только при ER-положительном статусе.")
        if self.trastuzumab and self.her2 != "positive":
            raise ValueError("Трастузумаб можно выбрать только при HER2-положительном статусе.")
        if self.bisphosphonates and self.menopause != "post":
            raise ValueError("В модели PREDICT польза бисфосфонатов применяется только в постменопаузе.")
        return self
