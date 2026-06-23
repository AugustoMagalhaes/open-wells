import io


def test_index(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"open-wells" in res.data


def test_calculate_basic(client):
    res = client.post(
        "/calculate",
        data={
            "well_0": "P-01",
            "x_0": "1000",
            "y_0": "2000",
            "z_0": "0",
            "wei_0": "500",
            "well_1": "I-01",
            "x_1": "1100",
            "y_1": "2100",
            "z_1": "0",
            "wei_1": "-200",
            "row_count": "2",
            "thousands": "",
            "decimal": ".",
        },
    )
    assert res.status_code == 200
    assert b"P-01" in res.data
    assert b"I-01" in res.data


def test_calculate_empty(client):
    res = client.post(
        "/calculate",
        data={
            "row_count": "0",
            "thousands": "",
            "decimal": ".",
        },
    )
    assert res.status_code == 200
    assert b"empty" in res.data.lower()


def test_calculate_no_injectors(client):
    res = client.post(
        "/calculate",
        data={
            "well_0": "P-01",
            "x_0": "1000",
            "y_0": "2000",
            "z_0": "0",
            "wei_0": "500",
            "row_count": "1",
            "thousands": "",
            "decimal": ".",
        },
    )
    assert res.status_code == 200
    assert b"injector" in res.data.lower()


def test_calculate_no_producers(client):
    res = client.post(
        "/calculate",
        data={
            "well_0": "I-01",
            "x_0": "1000",
            "y_0": "2000",
            "z_0": "0",
            "wei_0": "-200",
            "row_count": "1",
            "thousands": "",
            "decimal": ".",
        },
    )
    assert res.status_code == 200
    assert b"producer" in res.data.lower()


def test_calculate_invalid_well(client):
    res = client.post(
        "/calculate",
        data={
            "well_0": "X-01",
            "x_0": "1000",
            "y_0": "2000",
            "z_0": "0",
            "wei_0": "500",
            "well_1": "I-01",
            "x_1": "1100",
            "y_1": "2100",
            "z_1": "0",
            "wei_1": "-200",
            "row_count": "2",
            "thousands": "",
            "decimal": ".",
        },
    )
    assert res.status_code == 200
    assert b"X-01" in res.data


def test_import_csv_basic(client):
    csv_content = b"WELL,X,Y,Z,WEI\nP-01,1000,2000,0,500\nI-01,1100,2100,0,-200\n"
    res = client.post(
        "/import-csv",
        data={
            "sep": ",",
            "file": (io.BytesIO(csv_content), "test.csv"),
        },
        content_type="multipart/form-data",
    )
    assert res.status_code == 200
    assert b"P-01" in res.data
    assert b"I-01" in res.data


def test_import_csv_missing_columns(client):
    csv_content = b"WELL,X,Y\nP-01,1000,2000\n"
    res = client.post(
        "/import-csv",
        data={
            "sep": ",",
            "file": (io.BytesIO(csv_content), "test.csv"),
        },
        content_type="multipart/form-data",
    )
    assert res.status_code == 200
    assert b"Missing" in res.data


def test_import_csv_no_file(client):
    res = client.post(
        "/import-csv",
        data={"sep": ","},
        content_type="multipart/form-data",
    )
    assert res.status_code == 200
    assert b"No file" in res.data


def test_download(client):
    payload = [["P-01", "I-01"], ["P-02", "I-02"]]
    res = client.post("/download", json=payload)
    assert res.status_code == 200
    assert res.content_type == "text/csv; charset=utf-8"
    lines = res.data.decode().strip().splitlines()
    assert lines[0] == "PRODUCER,INJECTOR"
    assert lines[1] == "P-01,I-01"


def test_download_empty(client):
    res = client.post("/download", json=[])
    assert res.status_code == 200
    lines = res.data.decode().strip().splitlines()
    assert lines[0] == "PRODUCER,INJECTOR"
    assert len(lines) == 1


def test_get_prefs(client):
    res = client.get("/prefs")
    assert res.status_code == 200
    data = res.get_json()
    assert "decimal" in data
    assert "theme" in data
    assert "thousands" in data
    assert "csvsep" in data


def test_set_prefs(client, tmp_path, monkeypatch):
    import open_wells.prefs as prefs_module

    prefs_file = tmp_path / "prefs.json"
    monkeypatch.setattr(prefs_module, "PREFS_FILE", prefs_file)

    res = client.post("/prefs", json={"theme": "dark"})
    assert res.status_code == 204

    res = client.get("/prefs")
    data = res.get_json()
    assert data["theme"] == "dark"


def test_open_file_dialog(client):
    res = client.get("/open-file-dialog")
    assert res.status_code == 200
    data = res.get_json()
    assert "dir" in data


def test_save_file_dialog(client):
    res = client.get("/save-file-dialog")
    assert res.status_code == 200
    data = res.get_json()
    assert "dir" in data


def test_read_file(client, tmp_path):
    test_file = tmp_path / "test.csv"
    test_file.write_text("WELL,X,Y,Z,WEI\nP-01,1000,2000,0,500\n")
    res = client.post("/read-file", json={"path": str(test_file)})
    assert res.status_code == 200
    data = res.get_json()
    assert "content" in data
    assert "P-01" in data["content"]


def test_read_file_not_found(client):
    res = client.post("/read-file", json={"path": "/nonexistent/file.csv"})
    assert res.status_code == 400
    data = res.get_json()
    assert "error" in data


def test_calculate_exception(client, monkeypatch):
    import open_wells.app as app_module

    monkeypatch.setattr(
        app_module, "rows_to_df", lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("unexpected"))
    )
    res = client.post(
        "/calculate",
        data={
            "well_0": "P-01",
            "x_0": "1000",
            "y_0": "2000",
            "z_0": "0",
            "wei_0": "500",
            "well_1": "I-01",
            "x_1": "1100",
            "y_1": "2100",
            "z_1": "0",
            "wei_1": "-200",
            "row_count": "2",
            "thousands": "",
            "decimal": ".",
        },
    )
    assert res.status_code == 200
    assert b"unexpected" in res.data
