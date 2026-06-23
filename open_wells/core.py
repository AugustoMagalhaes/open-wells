import csv
import io
from collections import OrderedDict
from typing import Any

import numpy as np
import pandas as pd


def run_matching(df: pd.DataFrame) -> tuple[list[list[str]], str]:
    producers: dict[str, Any] = {}
    injectors: dict[str, Any] = {}

    for pos, (_, row) in enumerate(df.iterrows()):
        well = str(row["WELL"]).strip().upper()
        if not well or well[0] not in ("P", "I", "W"):
            return [], f"Row {pos + 1}: well '{well}' must start with P, I or W."
        target = injectors if well.startswith("I") else producers
        target[well] = {
            "COORD": np.array([row["X"], row["Y"], row["Z"]], dtype=float),
            "WEI": float(row["WEI"]),
        }

    if not producers:
        return [], "No producer well found (P or W)."
    if not injectors:
        return [], "No injector well found (I)."

    sorted_producers = OrderedDict(
        sorted(producers.items(), key=lambda i: i[1]["WEI"], reverse=True)
    )

    distances: dict[str, Any] = {}
    for producer, prod_data in sorted_producers.items():
        dists = {
            inj: float(np.linalg.norm(inj_data["COORD"] - prod_data["COORD"]))
            for inj, inj_data in injectors.items()
        }
        distances[producer] = OrderedDict(sorted(dists.items(), key=lambda item: item[1]))

    remaining_injs = list(injectors.keys())
    result: list[list[str]] = []
    pairs = list(distances.items())

    for idx, (prod, inj_distances) in enumerate(pairs):
        for inj in inj_distances:  # pragma: no branch
            if inj in remaining_injs:
                result.append([prod, inj])
                remaining_injs.remove(inj)
                break
            elif len(remaining_injs) == 0:  # pragma: no branch
                result.append([prod, "-"])
                break

        if idx == len(pairs) - 1 and len(remaining_injs) > 0:
            extras = [[prod, i] for i in inj_distances if i in remaining_injs]
            result = [*result, *extras]

    return result, ""


def parse_csv_content(content: str, sep: str) -> pd.DataFrame:
    reader = csv.reader(io.StringIO(content), delimiter=sep)
    rows = list(reader)

    if not rows:
        raise ValueError("Empty file.")

    headers = [h.strip().upper() for h in rows[0]]
    records = []

    for row in rows[1:]:
        if not any(cell.strip() for cell in row):
            continue
        record = {headers[i]: val.strip() for i, val in enumerate(row) if i < len(headers)}
        records.append(record)

    return pd.DataFrame(records)


def rows_to_df(rows: list[list[str]], thousands: str, decimal: str) -> pd.DataFrame:
    df = pd.DataFrame(rows, columns=["WELL", "X", "Y", "Z", "WEI"])
    for col in ["X", "Y", "Z", "WEI"]:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(thousands, "", regex=False)
            .str.replace(decimal, ".", regex=False)
            .replace("", "0")
        )
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    return df


def result_to_csv(result: list[list[str]]) -> str:
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(["PRODUCER", "INJECTOR"])
    for row in result:
        writer.writerow(row)
    return out.getvalue()
