from __future__ import annotations

import threading
import webbrowser

import uvicorn


URL = "http://127.0.0.1:8000"


def open_browser() -> None:
    webbrowser.open(URL)


if __name__ == "__main__":
    print(f"\nBreast Risk Hub запускается: {URL}")
    print("Для остановки нажмите Ctrl+C в этом окне.\n")
    threading.Timer(1.2, open_browser).start()
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)
