# Breast Risk Hub — версия 0.5.0

Исследовательский веб-инструмент единой формы для:

- PREDICT Breast v3.2;
- CRIB premenopausal (TEXT/SOFT, DRFI model);
- CRIB postmenopausal (BIG 1-98).

## Возможности

- единый ввод данных пациентки;
- расчет PREDICT на 5, 10 и 15 лет;
- гормонотерапия 5 или 10 лет;
- учет микрометастазов при одном положительном лимфоузле;
- расчет CRIB для пре- и постменопаузы;
- категории риска CRIB postmenopausal;
- таблица 5-летней DFS BIG 1-98 по вариантам эндокринотерапии;
- адаптивный интерфейс для компьютера, планшета и телефона.

## Статус

Инструмент остается исследовательским прототипом. До завершения полной
серии контрольных проверок он не предназначен для самостоятельного принятия
клинических решений.

## Публикация

Проект подготовлен для Render через `render.yaml` и `Dockerfile`.
Подробная инструкция: `DEPLOY_RENDER_RU.md`.

## Локальный запуск

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python run.py
```

## Тесты

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
```
