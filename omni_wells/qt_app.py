import json
import sys
import threading
import webbrowser
from pathlib import Path

from PyQt6.QtCore import QUrl
from PyQt6.QtWebEngineCore import QWebEngineDownloadRequest, QWebEnginePage
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QApplication, QFileDialog, QMainWindow

from omni_wells.app import _find_free_port, app
from omni_wells.prefs import load as load_prefs
from omni_wells.prefs import save as save_prefs


class WebPage(QWebEnginePage):
    def __init__(self, profile, parent, main_window):
        super().__init__(profile, parent)
        self._main_window = main_window

    def createWindow(self, win_type: QWebEnginePage.WebWindowType) -> "WebPage | None":
        self._pending_page = WebPage(self.profile(), self.parent(), self._main_window)
        self._pending_page.urlChanged.connect(self._open_external)
        return self._pending_page

    def _open_external(self, url: QUrl):
        if "127.0.0.1" not in url.toString():
            webbrowser.open(url.toString())
            self._main_window.activateWindow()
            self._main_window.raise_()
            QApplication.processEvents()
            view_page = self._main_window.centralWidget().page()
            view_page.runJavaScript(f"showToast('✓ Link {url.toString()} opened in browser')")
        self._pending_page.deleteLater()


def run_flask(port: int):
    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)


def handle_download(download: QWebEngineDownloadRequest, view: QWebEngineView):
    prefs = load_prefs()
    suggested = download.suggestedFileName()
    last_dir = prefs.get("last_download_dir", str(Path.home() / "Downloads"))

    path, _ = QFileDialog.getSaveFileName(
        None,
        "Save file",
        str(Path(last_dir) / suggested),
    )

    if path:
        save_prefs({"last_download_dir": str(Path(path).parent)})
        download.setDownloadDirectory(str(Path(path).parent))
        download.setDownloadFileName(Path(path).name)
        download.accept()
        download.isFinishedChanged.connect(
            lambda: view.page().runJavaScript(
                f"showToast({json.dumps('✓ Saved as ' + Path(path).name)})"
            )
        )
    else:
        download.cancel()


def handle_open_file(view: QWebEngineView, port: int):
    prefs = load_prefs()
    last_dir = prefs.get("last_import_dir", str(Path.home()))

    path, _ = QFileDialog.getOpenFileName(
        None,
        "Open CSV file",
        last_dir,
        "CSV files (*.csv);;Text files (*.txt);;All files (*.*)",
    )

    if not path:
        return

    save_prefs({"last_import_dir": str(Path(path).parent)})
    view.page().runJavaScript(f"triggerImportFromPath({json.dumps(path)})")


def main():
    port = _find_free_port()
    flask_thread = threading.Thread(target=run_flask, args=[port], daemon=True)
    flask_thread.start()

    qt_app = QApplication(sys.argv)

    window = QMainWindow()
    window.setWindowTitle("OmniWells")

    view = QWebEngineView()
    page = WebPage(view.page().profile(), view, window)
    view.setPage(page)

    page.profile().downloadRequested.connect(lambda dl: handle_download(dl, view))
    view.page().urlChanged.connect(lambda: view.page().runJavaScript("window._qtApp = true;"))

    view.setUrl(QUrl(f"http://127.0.0.1:{port}"))
    window.setCentralWidget(view)
    window.show()
    window.showMaximized()

    sys.exit(qt_app.exec())


if __name__ == "__main__":
    main()
