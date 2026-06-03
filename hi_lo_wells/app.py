import os
import socket
import threading
import webbrowser
from datetime import datetime

from flask import Flask, Response, render_template, request, session

from hi_lo_wells.core import parse_csv_content, result_to_csv, rows_to_df, run_matching

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "hi-lo-wells-dev")

COLS = ["WELL", "X", "Y", "Z", "WEI"]
DEFAULT_ROWS = 1


def _empty_rows(n: int) -> list[list[str]]:
    return [["", "", "", "", ""] for _ in range(n)]


@app.route("/")
def index():
    return render_template("index.html", rows=_empty_rows(DEFAULT_ROWS), cols=COLS)


@app.route("/import-csv", methods=["POST"])
def import_csv():
    file = request.files.get("file")
    sep = request.form.get("sep", ";")

    if not file:
        return render_template(
            "partials/table_body.html",
            rows=_empty_rows(DEFAULT_ROWS),
            cols=COLS,
            error="No file selected.",
        )

    content = file.read().decode("utf-8", errors="replace")
    try:
        df = parse_csv_content(content, sep=sep)
        required = {"WELL", "X", "Y", "Z", "WEI"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"Missing columns: {', '.join(sorted(missing))}")
        rows = df[COLS].fillna("").values.tolist()
        rows = [[str(v) for v in row] for row in rows]
    except Exception as exc:
        return render_template(
            "partials/table_body.html",
            rows=_empty_rows(DEFAULT_ROWS),
            cols=COLS,
            error=str(exc),
        )

    return render_template("partials/table_body.html", rows=rows, cols=COLS)


@app.route("/calculate", methods=["POST"])
def calculate():
    thousands = request.form.get("thousands", ",")
    decimal = request.form.get("decimal", ".")

    raw_rows = []
    for i in range(int(request.form.get("row_count", 0))):
        raw_rows.append(
            [
                request.form.get(f"well_{i}", ""),
                request.form.get(f"x_{i}", ""),
                request.form.get(f"y_{i}", ""),
                request.form.get(f"z_{i}", ""),
                request.form.get(f"wei_{i}", ""),
            ]
        )

    filled = [r for r in raw_rows if any(v.strip() for v in r)]
    if not filled:
        return render_template("partials/result.html", error="Table is empty.")

    try:
        df = rows_to_df(filled, thousands=thousands, decimal=decimal)
        result, err = run_matching(df)
        if err:
            return render_template("partials/result.html", error=err)
    except Exception as exc:
        return render_template("partials/result.html", error=str(exc))

    session["result"] = result
    return render_template("partials/result.html", result=result)


@app.route("/download", methods=["POST"])
def download():

    raw = request.get_json(silent=True) or []
    csv_content = result_to_csv(raw)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=result_{timestamp}.csv"},
    )


def _find_free_port(start: int = 5000) -> int:
    port = start
    while True:
        with socket.socket() as s:
            try:
                s.bind(("", port))
                return port
            except OSError:
                port += 1


def main():
    port = _find_free_port()
    url = f"http://127.0.0.1:{port}"

    if os.environ.get("HI_LO_WELLS_NO_BROWSER", "0") != "1":
        threading.Timer(1.2, webbrowser.open, args=[url]).start()

    print(f"  hi-lo-wells  →  {url}")
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)


if __name__ == "__main__":
    main()
