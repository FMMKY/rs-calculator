# Источники расчетных моделей

## PREDICT Breast v3

- Grootes I, Wishart GC, Pharoah PDP. An updated PREDICT breast cancer
  prognostic model including the benefits and harms of radiotherapy.
  NPJ Breast Cancer. 2024;10:6. DOI: 10.1038/s41523-024-00612-y.
- Derivation of the underlying model as implemented in PREDICT v3.0
  (предоставленный математический документ).
- Открытый R-пакет: pengpclab/PREDICTv3, лицензия MIT.

## CRIB — пременопауза

- Pagani O et al. Absolute Improvements in Freedom From Distant Recurrence
  to Tailor Adjuvant Endocrine Therapies for Premenopausal Women:
  Results From TEXT and SOFT. J Clin Oncol. 2020;38:1293–1303.
  DOI: 10.1200/JCO.18.01967.
- Использованы parameter estimates из таблицы модели DRFI.

## CRIB — постменопауза

- Viale G et al. Which patients benefit most from adjuvant aromatase
  inhibitors? Results using a composite measure of prognostic risk in
  the BIG 1-98 randomized trial. Ann Oncol. 2011;22:2201–2207.
  DOI: 10.1093/annonc/mdq738.
- Использованы коэффициенты Supplemental Table S1.

## PREDICT v3.2 implementation details

- WintonCentre/predictv30r:
  - `R/benefits32.R`
  - `inst/extdata/coefficients_v3.csv`
- WintonCentre/predict-v21-main:
  - `src/cljs/predict3/models/adapters/predict2.cljs`
  - `src/cljs/predict3/state/config.cljs`

The model year is fixed at 2017 in `benefits32.R`.
The 10-year hormone option uses the standard hormone coefficient through
year 10 and adds −0.301 in years 11–15.
One positive node with micrometastases only is mapped to 0.5 nodes by the
front-end adapter.

## CRIB postmenopausal treatment table

- Low risk (<0.66): 96%, 94%, 93%, 94%.
- Intermediate risk (0.66–1.53): 90%, 91%, 93%, 86%.
- High risk (>1.53): 80%, 76%, 74%, 69%.

Columns: letrozole; letrozole → tamoxifen; tamoxifen → letrozole;
tamoxifen.
