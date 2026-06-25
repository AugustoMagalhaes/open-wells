# OpenWells
<p align="center">
  <img src="docs/logo.svg" width="120" alt="OpenWells logo"/>
  <br/>
  <em>Wells' Opening Schedule Tool</em>
</p>

![Python](https://img.shields.io/badge/python-3.12+-blue?logo=python)
[![codecov](https://codecov.io/github/AugustoMagalhaes/omni-wells/graph/badge.svg?token=KR4BMAM5WX)](https://codecov.io/github/AugustoMagalhaes/omni-wells)
![CI](https://github.com/AugustoMagalhaes/omni-wells/actions/workflows/ci.yaml/badge.svg)
![License](https://img.shields.io/badge/license-MIT-green)


---

## Background

OpenWells implements the fast well opening schedule procedure proposed by Diniz et al. (2024) ([doi:10.1016/j.geoen.2024.213179](https://doi.org/10.1016/j.geoen.2024.213179)) and updated by Diniz et al. (2026) ([doi:10.1007/s40430-025-06230-4](https://doi.org/10.1007/s40430-025-06230-4)).

The procedure addresses a common challenge in reservoir management: defining the optimal sequence in which producer and injector wells should be opened to improve field recovery. Rather than solving a complex combinatorial optimization problem, the method uses a fast heuristic based on two criteria:

- **Economic index (PWEI / IWEI)**: producers are prioritized in descending order of their economic index, ensuring the most profitable wells are opened first.
- **3D Cartesian distance**: for each prioritized producer, the nearest unassigned injector (by Euclidean distance between wellheads) is assigned, establishing the producer–injector pairs.

The user provides a list of wells with their wellhead Cartesian coordinates (X, Y, Z) and the economic index for each well, with sign convention: **positive for producers (PWEI)**, **negative for injectors (IWEI)**. OpenWells then generates the ordered sequence of producer–injector pairs, which can be used to evaluate well relationships and define the opening schedule significantly faster than full optimization approaches.

---

## Quickstart

### Requirements

- Python 3.12+
- Windows / macOS: PyPI wheels include all required Qt libraries for Windows and macOS.
- Linux:

  **Ubuntu / Debian**
```bash
  sudo apt install libglib2.0-0 libnss3 libx11-6 python3-pyqt6 python3-pyqt6.qtwebengine
```

  **Fedora / RHEL / CentOS**
```bash
  sudo dnf install glib2 nss libX11 python3-pyqt6 python3-pyqt6-webengine
```

  **Arch Linux / Manjaro**
```bash
  sudo pacman -S python-pyqt6 python-pyqt6-webengine
```

  **openSUSE**
```bash
  sudo zypper install libglib-2_0-0 mozilla-nss libX11-6 python3-qt6 python3-qt6-webengine
```

### Installation

Install OpenWells using your preferred package manager. After installation, launch the application by running `omni-wells`.

**pipx** *(recommended for most users; installs the application in an isolated environment)*
```bash
pipx install omni-wells
omni-wells
```

**pip**
```bash
pip install omni-wells
omni-wells
```

**uv**
```bash
uv tool install omni-wells
omni-wells
```

A native desktop window opens automatically and no browser configuration is needed. The interface is built with **PyQt6 + WebEngine**, serving a **Flask** application internally. This means the UI runs as a web app inside a desktop window, combining the flexibility of web technologies with the convenience of a native application.

### Getting Started

Not sure where to start? The application ships with a built-in sample dataset:

1. In the sidebar, under **Sample**, click **↓ Download sample case** to get a ready-to-use CSV file.
2. Click **📂 Open CSV file** and select the downloaded file.
3. The table is populated automatically with 20 producers and 20 injectors.
4. Click **⚙ Evaluate data**: the result panel on the right shows the producer–injector pairs instantly.
5. Click **⬇ Download CSV** to save the result, or the copy icon to copy it to the clipboard.

---

## Using the application

### Data entry

There are three ways to load your data:

**Manual input**: click any cell in the table and type directly. Navigate with arrow keys or Enter to move between cells. Click **add row** to add new rows if needed.

**Paste from Excel or any spreadsheet**: select a cell in the table, copy your data from Excel (including the header row), and press `Ctrl+V`. OpenWells detects the header and delimiter automatically and fills the table.

**Import a CSV file**: click **📂 Open CSV file**. Before importing, configure the separators to match your file format (see below).

### Input format

The table expects five columns:

| WELL | X | Y | Z | WEI |
|------|---|---|---|-----|
| P-01 | 1000.25 | 2000.50 | 100.75 | 950.33 |
| Wildcat | 5000.10 | 8000.80 | 200.40 | 900.17 |
| I-01 | 1100.30 | 2100.60 | 101.85 | -200.44 |

- **WELL**: well name. Must start with `P` or `W` for producers, `I` for injectors. Displayed in blue for producers, orange for injectors.
- **X, Y, Z**: Cartesian coordinates of the wellhead.
- **WEI**: economic index. Positive for producers (PWEI), negative for injectors (IWEI).

### Separator configuration

In the sidebar under **Number format** and **Import CSV**, you can configure:

- **Decimal separator**: period `.` (default, international standard) or comma `,` (Brazilian/European standard)
- **Thousands separator**: none (default), comma `,` or period `.`
- **Column separator**: comma `,` (default), semicolon `;` or Tab

These settings prevent conflicts automatically: if two separators would clash, the conflicting option is disabled. **All separator preferences are persisted between sessions**, so you only need to configure them once.

### Managing rows

- **+ New row**: adds a blank row at the bottom
- **+ add row**: button at the bottom of the table, same effect
- **Checkboxes**: select individual rows or all at once with the header checkbox (`Ctrl+A` while a cell is focused selects all)
- **✕ Delete selected**: removes selected rows, with a confirmation modal showing the data about to be deleted
- **🗑 Clear table**: removes all rows and resets the table

### Result

After clicking **⚙ Evaluate data**, the right panel shows the ordered producer–injector pairs. From there:

- **⬇ Download CSV**: saves the result as `result_<timestamp>.csv`
- **Copy icon**: copies the result to the clipboard in CSV format

### Dark / Light mode

Click **☾ Dark** / **☀ Light** in the top-right corner to toggle the theme. The chosen theme **persists across sessions**, so the next time you open the application it remembers your preference.

---

## Development

Only Docker and Make are required — no local Python installation needed.

```bash
git clone https://github.com/AugustoMagalhaes/omni-wells.git
cd omni-wells
make build
make up
```

Access at `http://localhost:5000`.

| Command | Description |
|---------|-------------|
| `make build` | Build the Docker image |
| `make up` | Start the development server |
| `make up-bg` | Start in background |
| `make down` | Stop and remove containers |
| `make logs` | Follow container logs |
| `make shell` | Open bash inside the container |
| `make lint` | Run ruff check |
| `make format` | Run ruff format |
| `make test` | Run pytest |
| `make dist` | Build wheel and sdist |
| `make clean` | Remove cache and build artifacts |

---

## Tech stack

| Layer | Technology |
|-------|-----------|
| Desktop wrapper | PyQt6 + QtWebEngine |
| Backend | Flask + HTMX |
| Data processing | pandas + numpy |
| Styling | Vanilla CSS with CSS variables |
| Tests | pytest + pytest-cov |
| Lint | ruff |
| CI | GitHub Actions + Codecov |

---

## References

- Diniz et al. (2024). *A fast procedure for well opening schedule in oil fields.* Geoenergy Science and Engineering. [doi:10.1016/j.geoen.2024.213179](https://doi.org/10.1016/j.geoen.2024.213179)
- Diniz et al. (2026). *Updated well opening schedule procedure.* Journal of the Brazilian Society of Mechanical Sciences and Engineering. [doi:10.1007/s40430-025-06230-4](https://doi.org/10.1007/s40430-025-06230-4)

---

## License

MIT © [Augusto Magalhães](https://github.com/AugustoMagalhaes)
