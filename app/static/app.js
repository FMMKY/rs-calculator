"use strict";

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("calculator-form");
  const errorBox = document.getElementById("form-error");
  const statusBox = document.getElementById("interface-status");
  const resultsBox = document.getElementById("results");
  const cribBox = document.getElementById("crib-result");
  const predictBox = document.getElementById("predict-result");
  const tennesseeBox = document.getElementById("tennessee-result");
  const calculateButton = document.getElementById("brh-calculate-button");
  const rtCheckbox = document.getElementById("radiotherapy");
  const heartDose = document.getElementById("heart_dose_gy");
  const menopause = document.querySelector("[name='menopause']");
  const her2 = document.querySelector("[name='her2']");
  const erPercent = document.querySelector("[name='er_percent']");
  const endocrine = document.getElementById("endocrine_therapy");
  const trastuzumab = document.querySelector("[name='trastuzumab']");
  const bisphosphonates = document.querySelector("[name='bisphosphonates']");
  const priorChemoField = document.getElementById("prior-chemo-field");
  const positiveNodes = document.getElementById("positive_nodes");
  const micrometastasesField = document.getElementById("micrometastases-field");
  const micrometastases = document.getElementById("micrometastases");

  function escapeHtml(value) {
    return String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#039;");
  }

  function warningsHtml(warnings) {
    if (!warnings || warnings.length === 0) return "";
    return `<ul class="warning-list">${warnings.map(item => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`;
  }

  function updateConditionalFields() {
    heartDose.disabled = !rtCheckbox.checked;
    if (!rtCheckbox.checked) heartDose.value = "0";

    const isPost = menopause.value === "post";
    bisphosphonates.disabled = !isPost;
    if (!isPost) bisphosphonates.checked = false;

    const isHer2Positive = her2.value === "positive";
    trastuzumab.disabled = !isHer2Positive;
    if (!isHer2Positive) trastuzumab.checked = false;

    const isErPositive = Number(erPercent.value) >= 1;
    if (!isErPositive) endocrine.value = "none";
    endocrine.disabled = !isErPositive;

    const hasOnePositiveNode = Number(positiveNodes.value) === 1;
    micrometastasesField.hidden = !hasOnePositiveNode;
    if (!hasOnePositiveNode) micrometastases.value = "no";

    priorChemoField.hidden = menopause.value !== "pre";
  }

  [rtCheckbox, menopause, her2, erPercent, positiveNodes].forEach(element => {
    element.addEventListener("change", updateConditionalFields);
    element.addEventListener("input", updateConditionalFields);
  });
  updateConditionalFields();

  function renderDfsTable(cribData) {
    const dfs = cribData.postmenopausal_dfs;
    if (!dfs) return "";
    const tableRows = dfs.rows.map(row => {
      const activeClass = row.risk_code === dfs.active_risk_code ? "active-risk-row" : "";
      const values = [row.letrozole, row.letrozole_to_tamoxifen, row.tamoxifen_to_letrozole, row.tamoxifen];
      const maxValue = Math.max(...values);
      const cell = value => `<td class="${value === maxValue ? "best-dfs-cell" : ""}">${value}%</td>`;
      return `<tr class="${activeClass}"><td>${escapeHtml(row.risk_label)}</td><td>${escapeHtml(row.parameter_estimate)}</td>${cell(row.letrozole)}${cell(row.letrozole_to_tamoxifen)}${cell(row.tamoxifen_to_letrozole)}${cell(row.tamoxifen)}</tr>`;
    }).join("");
    return `<section class="crib-dfs-section"><h3>${escapeHtml(dfs.title)}</h3><div class="crib-treatment-summary"><strong>${escapeHtml(dfs.interpretation)}</strong><p>${escapeHtml(dfs.caution)}</p></div><div class="table-scroll"><table class="dfs-table"><thead><tr><th>Группа риска</th><th>CRIB</th><th>Летрозол</th><th>Летрозол → тамоксифен</th><th>Тамоксифен → летрозол</th><th>Тамоксифен</th></tr></thead><tbody>${tableRows}</tbody></table></div><p class="meta dfs-footnote">Выделена строка рассчитанной группы риска; подчеркнуто наибольшее опубликованное значение внутри каждой группы.</p></section>`;
  }

  function renderCrib(data) {
    if (data.available === false) {
      cribBox.innerHTML = `<h2>CRIB</h2><div class="badge not-applicable-badge">Не применимо</div><div class="crib-unavailable"><strong>CRIB не рассчитывается для введенного клинического случая.</strong><p>${escapeHtml(data.reason)}</p></div><p class="meta">Остальные модели рассчитаны независимо.</p>`;
      return;
    }
    const rows = data.contributions.map(item => `<tr><td>${escapeHtml(item.factor)}</td><td>${escapeHtml(item.category)}</td><td>${Number(item.coefficient).toFixed(2)}</td></tr>`).join("");
    const riskLabel = data.risk_label ? `<div class="risk-classification risk-${escapeHtml(data.risk_code)}"><span>Группа риска</span><strong>${escapeHtml(data.risk_label)}</strong></div>` : "";
    cribBox.innerHTML = `<h2>CRIB</h2><div class="badge">${escapeHtml(data.applicability)}</div><div class="score"><span>Composite risk</span><strong>${Number(data.score).toFixed(2)}</strong>${data.risk_band ? `<div>${escapeHtml(data.risk_band)}</div>` : ""}</div>${riskLabel}<p class="meta">${escapeHtml(data.model)}</p><p class="meta">${escapeHtml(data.endpoint)}</p>${data.interpretation_cohort ? `<p class="meta"><strong>${escapeHtml(data.interpretation_cohort)}</strong></p>` : ""}<table><thead><tr><th>Показатель</th><th>Категория</th><th>Вклад</th></tr></thead><tbody>${rows}</tbody></table>${renderDfsTable(data)}${warningsHtml(data.warnings)}`;
  }

  function renderPredict(data) {
    const panels = data.horizons.map((horizon, index) => {
      const rows = horizon.rows.map(item => `<tr><td>${escapeHtml(item.treatment)}</td><td>${item.additional_benefit === null ? "—" : `${Number(item.additional_benefit) >= 0 ? "+" : ""}${Number(item.additional_benefit).toFixed(1)}%`}</td><td><strong>${item.survival_display}%</strong><span class="exact-value"> (${Number(item.survival_exact).toFixed(2)}%)</span></td></tr>`).join("");
      return `<div class="predict-horizon-panel ${index === 0 ? "active" : ""}" data-year="${horizon.year}"><p class="meta">Ожидаемая общая выживаемость через ${horizon.year} лет после последовательно добавляемых выбранных методов лечения.</p><table><thead><tr><th>Лечение</th><th>Дополнительная польза в комбинации</th><th>Общая выживаемость</th></tr></thead><tbody>${rows}</tbody></table></div>`;
    }).join("");
    const tabs = data.horizons.map((horizon, index) => `<button type="button" class="horizon-tab ${index === 0 ? "active" : ""}" data-year="${horizon.year}">${horizon.year} лет</button>`).join("");
    predictBox.innerHTML = `<h2>PREDICT Breast v3</h2><div class="badge success-badge">${escapeHtml(data.status)}</div><p class="meta">${escapeHtml(data.model)}</p><div class="predict-input-summary"><strong>Как данные интерпретированы PREDICT</strong><div>ER: ${escapeHtml(data.status_mapping.ER)}</div><div>PgR: ${escapeHtml(data.status_mapping.PgR)}</div><div>Ki-67: ${escapeHtml(data.status_mapping["Ki-67"])}</div><div>Выявление: ${escapeHtml(data.status_mapping["Способ выявления"])}</div><div>Узлы в модели: ${escapeHtml(data.status_mapping["Узлы PREDICT"])}</div><div>Гормонотерапия: ${escapeHtml(data.status_mapping.Гормонотерапия)}</div></div><div class="horizon-tabs">${tabs}</div>${panels}${warningsHtml(data.warnings)}`;
    predictBox.querySelectorAll(".horizon-tab").forEach(button => {
      button.addEventListener("click", () => {
        const year = button.dataset.year;
        predictBox.querySelectorAll(".horizon-tab").forEach(item => item.classList.toggle("active", item === button));
        predictBox.querySelectorAll(".predict-horizon-panel").forEach(panel => panel.classList.toggle("active", panel.dataset.year === year));
      });
    });
  }

  function renderTennessee(data) {
    if (data.available === false) {
      tennesseeBox.innerHTML = `<h2>Tennessee Oncotype DX Nomogram</h2><div class="badge not-applicable-badge">Не применимо</div><div class="crib-unavailable"><strong>Номограмма не рассчитывается для введенного случая.</strong><p>${escapeHtml(data.reason)}</p></div><p class="meta">PREDICT и CRIB рассчитаны независимо, если применимы.</p>`;
      return;
    }

    const mapping = Object.entries(data.input_mapping).map(([key, value]) => `<div><span>${escapeHtml(key)}</span><strong>${escapeHtml(value)}</strong></div>`).join("");
    tennesseeBox.innerHTML = `
      <h2>Tennessee Oncotype DX Nomogram</h2>
      <div class="badge success-badge">${escapeHtml(data.applicability)}</div>
      <div class="oncotype-probability-grid">
        <div class="oncotype-probability low-score"><span>RS 0–25</span><strong>${Number(data.low_risk.probability).toFixed(2)}%</strong><p>Вероятность низкого Recurrence Score</p></div>
        <div class="oncotype-probability high-score"><span>RS 26–100</span><strong>${Number(data.high_risk.probability).toFixed(2)}%</strong><p>Вероятность высокого Recurrence Score</p></div>
      </div>
      <div class="tennessee-mapping"><strong>Параметры модели</strong>${mapping}</div>
      ${warningsHtml(data.warnings)}
    `;
  }

  function payloadFromForm() {
    const data = new FormData(form);
    return {
      age: Number(data.get("age")), menopause: data.get("menopause"), smoker: data.get("smoker"), distant_metastasis: data.get("distant_metastasis") === "yes",
      tumor_size_mm: Number(data.get("tumor_size_mm")), positive_nodes: Number(data.get("positive_nodes")), micrometastases: Number(data.get("positive_nodes")) === 1 ? data.get("micrometastases") : "not_applicable",
      grade: Number(data.get("grade")), histology: data.get("histology"), screen_detected: data.get("screen_detected"), er_percent: Number(data.get("er_percent")), pr_percent: Number(data.get("pr_percent")), her2: data.get("her2"), ki67_percent: Number(data.get("ki67_percent")), vascular_invasion: data.get("vascular_invasion"), prior_chemotherapy: data.get("prior_chemotherapy") || "no",
      endocrine_therapy: endocrine.value || "none", chemotherapy: data.get("chemotherapy"), radiotherapy: data.has("radiotherapy"), heart_dose_gy: data.has("radiotherapy") ? Number(data.get("heart_dose_gy")) : 0, trastuzumab: data.has("trastuzumab"), bisphosphonates: data.has("bisphosphonates"),
    };
  }

  async function runCalculation() {
    errorBox.hidden = true;
    resultsBox.hidden = true;
    if (!form.reportValidity()) return;
    calculateButton.disabled = true;
    calculateButton.textContent = "Рассчитываю…";
    statusBox.textContent = "Выполняется расчет…";
    try {
      const response = await fetch("/api/calculate", {method: "POST", cache: "no-store", headers: {"Content-Type": "application/json"}, body: JSON.stringify(payloadFromForm())});
      const data = await response.json();
      if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail));
      renderCrib(data.crib);
      renderPredict(data.predict);
      renderTennessee(data.tennessee_oncotype);
      resultsBox.hidden = false;
      statusBox.textContent = "Расчет выполнен.";
      resultsBox.scrollIntoView({behavior: "smooth", block: "start"});
    } catch (error) {
      errorBox.textContent = error.message;
      errorBox.hidden = false;
      statusBox.textContent = "Расчет не выполнен.";
    } finally {
      calculateButton.disabled = false;
      calculateButton.textContent = "Рассчитать все модели";
    }
  }

  calculateButton.addEventListener("click", runCalculation);
  form.addEventListener("submit", event => { event.preventDefault(); runCalculation(); });

  fetch("/api/health", {cache: "no-store"}).then(response => response.json()).then(health => { statusBox.textContent = `Готово к расчету. Версия сервера ${health.version}.`; }).catch(() => { statusBox.textContent = "Сервер не отвечает."; calculateButton.disabled = true; });
});
