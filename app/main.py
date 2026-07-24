from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from app.models.crib_post import calculate_crib_post
from app.models.crib_pre import calculate_crib_pre
from app.models.predict_v3 import calculate_predict
from app.schemas import PatientInput


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="Breast Risk Hub",
    version="0.5.1",
    description=(
        "Исследовательский веб-инструмент для PREDICT Breast v3.2 и CRIB."
    ),
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = (
        "camera=(), microphone=(), geolocation=(), payment=()"
    )
    response.headers["X-Robots-Tag"] = "noindex, nofollow"
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store, max-age=0"
    return response


@app.get("/robots.txt", include_in_schema=False)
def robots() -> PlainTextResponse:
    return PlainTextResponse("User-agent: *\nDisallow: /\n")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(
        STATIC_DIR / "index.html",
        headers={"Cache-Control": "no-store, max-age=0"},
    )


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "version": "0.5.1"}


def crib_not_applicable(reason: str) -> dict:
    return {
        "available": False,
        "applicability": "не применимо",
        "model": "CRIB",
        "reason": reason,
        "warnings": [],
    }


def calculate_crib_independently(patient: PatientInput) -> dict:
    if patient.er_percent < 1 and patient.pr_percent < 1:
        return crib_not_applicable(
            "CRIB разработан для гормонорецептор-положительного раннего "
            "рака молочной железы. При ER 0% и PgR 0% индекс не рассчитывается."
        )

    try:
        result = (
            calculate_crib_pre(patient)
            if patient.menopause == "pre"
            else calculate_crib_post(patient)
        )
        result["available"] = True
        return result
    except ValueError as exc:
        return crib_not_applicable(str(exc))


@app.post("/api/calculate")
def calculate(patient: PatientInput) -> dict:
    try:
        # PREDICT and CRIB are independent models. A CRIB limitation must not
        # prevent calculation of PREDICT.
        predict = calculate_predict(patient)
        crib = calculate_crib_independently(patient)

        return {
            "input_summary": {
                "age": patient.age,
                "menopause": patient.menopause,
                "tumor_size_mm": patient.tumor_size_mm,
                "positive_nodes": patient.positive_nodes,
                "micrometastases": patient.micrometastases,
                "grade": patient.grade,
                "er_percent": patient.er_percent,
                "pr_percent": patient.pr_percent,
                "her2": patient.her2,
                "ki67_percent": patient.ki67_percent,
            },
            "crib": crib,
            "predict": predict,
            "version": "0.5.1",
        }
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
