import pandas as pd
import pytest

from omni_wells.core import parse_csv_content, result_to_csv, rows_to_df, run_matching

FIXTURES = "tests/fixtures"


def make_df(rows):
    return pd.DataFrame(rows, columns=["WELL", "X", "Y", "Z", "WEI"])


def test_run_matching_basic():
    df = make_df(
        [
            ["P-01", 1000, 2000, 0, 500],
            ["P-02", 5000, 5000, 0, 300],
            ["P-03", 9000, 2000, 0, 100],
            ["I-01", 1100, 2100, 0, -200],
            ["I-02", 5100, 5100, 0, -150],
            ["I-03", 9100, 2100, 0, -100],
        ]
    )
    result, err = run_matching(df)
    assert err == ""
    assert result == [["P-01", "I-01"], ["P-02", "I-02"], ["P-03", "I-03"]]


def test_run_matching_fixture():
    df = pd.read_csv(f"{FIXTURES}/test_input.csv", sep=",")
    df.columns = [c.strip().upper() for c in df.columns if isinstance(c, str)]
    result, err = run_matching(df)
    assert err == ""
    expected = pd.read_csv(f"{FIXTURES}/test_output.csv")
    expected_list = expected.values.tolist()
    assert result == expected_list


def test_run_matching_no_producers():
    df = make_df(
        [
            ["I-01", 1000, 2000, 0, -200],
            ["I-02", 5000, 5000, 0, -150],
        ]
    )
    result, err = run_matching(df)
    assert result == []
    assert "no producer well found (p or w)." == err.lower()


def test_run_matching_no_injectors():
    df = make_df(
        [
            ["P-01", 1000, 2000, 0, 500],
            ["P-02", 5000, 5000, 0, 300],
        ]
    )
    result, err = run_matching(df)
    assert result == []
    assert "no injector well found (i)." == err.lower()


def test_run_matching_invalid_well():
    df = make_df(
        [
            ["X-01", 1000, 2000, 0, 500],
            ["I-01", 1100, 2100, 0, -200],
        ]
    )
    result, err = run_matching(df)
    assert result == []
    assert "Row 1: well 'X-01' must start with P, I or W." == err


def test_run_matching_wei_ordering():
    df = make_df(
        [
            ["P-01", 9000, 9000, 0, 100],
            ["P-02", 1000, 1000, 0, 900],
            ["I-01", 1100, 1100, 0, -200],
            ["I-02", 9100, 9100, 0, -100],
        ]
    )
    result, err = run_matching(df)
    assert err == ""
    assert result[0][0] == "P-02"
    assert result[0][1] == "I-01"


def test_run_matching_w_prefix():
    df = make_df(
        [
            ["W-01", 1000, 2000, 0, 500],
            ["I-01", 1100, 2100, 0, -200],
        ]
    )
    result, err = run_matching(df)
    assert err == ""
    assert result == [["W-01", "I-01"]]


def test_parse_csv_content_columns():
    df = parse_csv_content(
        "WELL,X,Y,Z,WEI\nP-01,1000,2000,0,500\n",
        sep=",",
    )
    assert list(df.columns) == ["WELL", "X", "Y", "Z", "WEI"]


def test_parse_csv_content_rows():
    df = parse_csv_content(
        "WELL,X,Y,Z,WEI\nP-01,1000,2000,0,500\nI-01,1100,2100,0,-200\n",
        sep=",",
    )
    assert len(df) == 2
    assert df.iloc[0]["WELL"] == "P-01"


def test_parse_csv_content_missing_columns():
    with pytest.raises(Exception):
        df = parse_csv_content(
            "WELL,X,Y\nP-01,1000,2000\n",
            sep=",",
        )
        required = {"WELL", "X", "Y", "Z", "WEI"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"Missing columns: {missing}")


def test_result_to_csv_header():
    csv = result_to_csv([["P-01", "I-01"]])
    assert csv.startswith("PRODUCER,INJECTOR")


def test_result_to_csv_rows():
    csv = result_to_csv([["P-01", "I-01"], ["P-02", "I-02"]])
    lines = csv.strip().split("\n")
    assert len(lines) == 3
    assert lines[1] == "P-01,I-01"
    assert lines[2] == "P-02,I-02"


def test_result_to_csv_empty():
    csv = result_to_csv([])
    lines = csv.strip().split("\n")
    assert len(lines) == 1
    assert lines[0] == "PRODUCER,INJECTOR"


def test_rows_to_df_conversion():
    rows = [["P-01", "1.000,50", "2.000,75", "0", "500,33"]]
    df = rows_to_df(rows, thousands=".", decimal=",")
    assert df.iloc[0]["X"] == pytest.approx(1000.50)
    assert df.iloc[0]["WEI"] == pytest.approx(500.33)


def test_rows_to_df_invalid_numeric():
    rows = [["P-01", "abc", "2000", "0", "500"]]
    df = rows_to_df(rows, thousands="", decimal=".")
    assert df.iloc[0]["X"] == 0.0


def test_run_matching_more_producers_than_injectors():
    df = make_df(
        [
            ["P-01", 1000, 2000, 0, 900],
            ["P-02", 5000, 5000, 0, 800],
            ["P-03", 9000, 2000, 0, 700],
            ["I-01", 1100, 2100, 0, -200],
        ]
    )
    result, err = run_matching(df)
    assert err == ""
    assert ["P-01", "I-01"] in result
    assert any(r[1] == "-" for r in result)


def test_run_matching_last_producer_gets_closest_remaining_injector():
    df = make_df(
        [
            ["P-01", 1000, 2000, 0, 900],
            ["P-02", 9000, 9000, 0, 100],
            ["I-01", 1100, 2100, 0, -200],
            ["I-02", 9100, 9100, 0, -150],
            ["I-03", 9200, 9200, 0, -100],
        ]
    )
    result, err = run_matching(df)
    assert err == ""
    assert ["P-01", "I-01"] in result
    assert ["P-02", "I-02"] in result


def test_parse_csv_content_empty_file():
    with pytest.raises(ValueError, match="Empty file"):
        parse_csv_content("", sep=",")


def test_parse_csv_content_skips_empty_rows():
    df = parse_csv_content(
        "WELL,X,Y,Z,WEI\nP-01,1000,2000,0,500\n\n\n",
        sep=",",
    )

    assert len(df) == 1


def test_run_matching_more_injectors_than_producers():
    df = make_df(
        [
            ["P-01", 1000, 2000, 0, 900],
            ["I-01", 1100, 2100, 0, -200],
            ["I-02", 1200, 2200, 0, -150],
            ["I-03", 1300, 2300, 0, -100],
        ]
    )
    result, err = run_matching(df)
    assert err == ""
    assert result[0][0] == "P-01"
    assert result[0][1] == "I-01"
    assert len(result) >= 2
    all_producers = {r[0] for r in result}
    assert all_producers == {"P-01"}


def test_run_matching_producer_no_match_remaining_empty():
    df = make_df(
        [
            ["P-01", 1000, 2000, 0, 900],
            ["P-02", 5000, 5000, 0, 800],
            ["I-01", 1100, 2100, 0, -200],
        ]
    )
    result, err = run_matching(df)
    assert err == ""
    assert ["P-01", "I-01"] in result
    assert ["P-02", "-"] in result
