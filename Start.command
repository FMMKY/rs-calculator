#!/bin/bash
set -e
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 не найден."
  echo "Установите Python 3.11 или новее с https://www.python.org/downloads/"
  read -p "Нажмите Enter, чтобы закрыть окно..."
  exit 1
fi

if [ ! -d ".venv" ]; then
  echo "Создаю локальное окружение Python..."
  python3 -m venv .venv
fi

source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python run.py
