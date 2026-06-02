const COLS = ["WELL", "X", "Y", "Z", "WEI"];

document.addEventListener("DOMContentLoaded", () => {
    const saved = localStorage.getItem("theme") || "light";
    document.documentElement.dataset.theme = saved;
    updateThemeBtn(saved);
});

function toggleTheme() {
    const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    localStorage.setItem("theme", next);
    updateThemeBtn(next);
}

function updateThemeBtn(theme) {
    const btn = document.getElementById("theme-btn");
    if (btn) btn.textContent = theme === "dark" ? "☀ Light" : "☾ Dark";
}

function colorWell(inp) {
    const v = inp.value.trim().toUpperCase();
    inp.className = v.startsWith("I") ? "well-i" : (v ? "well-p" : "");
}

function navKey(e) {
    const inp = e.target;
    const td = inp.parentElement;
    const tr = td.parentElement;
    const colIdx = [...tr.cells].indexOf(td);

    if (e.key === "Enter" || e.key === "ArrowDown") {
        e.preventDefault();
        let next = tr.nextElementSibling;
        if (!next) { addRow(); next = tr.nextElementSibling; }
        next.cells[colIdx]?.querySelector("input[type='text']")?.focus();
    } else if (e.key === "ArrowUp") {
        e.preventDefault();
        tr.previousElementSibling?.cells[colIdx]?.querySelector("input[type='text']")?.focus();
    } else if (e.key === "ArrowRight" && inp.selectionStart === inp.value.length) {
        tr.cells[colIdx + 1]?.querySelector("input[type='text']")?.focus();
    } else if (e.key === "ArrowLeft" && inp.selectionStart === 0) {
        tr.cells[colIdx - 1]?.querySelector("input[type='text']")?.focus();
    }
}

function syncImportMeta() {
    document.getElementById("imp-thousands").value = document.getElementById("thousands").value;
    document.getElementById("imp-decimal").value = document.getElementById("decimal").value;
    document.getElementById("imp-sep").value = document.getElementById("csvsep").value;
}

function updateRowCount() {
    document.getElementById("row-count").value =
        document.getElementById("tbody").rows.length;
}

function reindex() {
    const rows = document.getElementById("tbody").rows;
    for (let i = 0; i < rows.length; i++) {
        rows[i].cells[0].textContent = i + 1;
        ["well", "x", "y", "z", "wei"].forEach(name => {
            const inp = rows[i].querySelector(`input[name^="${name}_"]`);
            if (inp) inp.name = `${name}_${i}`;
        });
    }
}

function addRow() {
    const tbody = document.getElementById("tbody");
    const idx = tbody.rows.length;
    const tr = document.createElement("tr");

    const rn = document.createElement("td");
    rn.className = "rn";
    rn.textContent = idx + 1;
    tr.appendChild(rn);

    const tdCheck = document.createElement("td");
    tdCheck.className = "td-check";
    const cb = document.createElement("input");
    cb.type = "checkbox";
    cb.addEventListener("change", () => {
        tr.classList.toggle("row-selected", cb.checked);
        syncSelectAll();
    });
    tdCheck.appendChild(cb);
    tr.appendChild(tdCheck);

    ["well", "x", "y", "z", "wei"].forEach(name => {
        const td = document.createElement("td");
        const inp = document.createElement("input");
        inp.type = "text";
        inp.name = `${name}_${idx}`;
        inp.setAttribute("autocomplete", "off");
        inp.setAttribute("spellcheck", "false");
        inp.addEventListener("keydown", navKey);
        if (name === "well") inp.addEventListener("input", () => colorWell(inp));
        td.appendChild(inp);
        tr.appendChild(td);
    });

    tbody.appendChild(tr);
    updateRowCount();
}

function deleteSelected() {
    const tbody = document.getElementById("tbody");
    [...tbody.rows]
        .filter(tr => tr.querySelector('input[type="checkbox"]')?.checked)
        .forEach(tr => tr.remove());
    reindex();
    updateRowCount();
    syncSelectAll();
}

function toggleSelectAll(master) {
    const tbody = document.getElementById("tbody");
    [...tbody.rows].forEach(tr => {
        const cb = tr.querySelector('input[type="checkbox"]');
        if (!cb) return;
        cb.checked = master.checked;
        tr.classList.toggle("row-selected", master.checked);
    });
}

function syncSelectAll() {
    const tbody = document.getElementById("tbody");
    const all = [...tbody.rows]
        .map(tr => tr.querySelector('input[type="checkbox"]'))
        .filter(Boolean);
    const master = document.getElementById("select-all");
    if (!master) return;
    master.checked = all.length > 0 && all.every(cb => cb.checked);
    master.indeterminate = !master.checked && all.some(cb => cb.checked);
}

function clearTable(refill = true) {
    document.getElementById("tbody").innerHTML = "";
    document.getElementById("result-area").innerHTML = "";
    document.getElementById("dl-btn").style.display = "none";
    const master = document.getElementById("select-all");
    if (master) { master.checked = false; master.indeterminate = false; }
    if (refill) {
        addRow();
    }
}

function detectDelimiter(line) {
    if (line.includes("\t")) return "\t";
    if (line.includes(";")) return ";";
    return ",";
}

function parseClipboard(text) {
    const lines = text.trim().split(/\r?\n/);
    const delim = detectDelimiter(lines[0]);
    const parsed = lines.map(l => l.split(delim));
    const firstUpper = parsed[0].map(v => v.trim().toUpperCase());
    const fieldOrder = ["WELL", "X", "Y", "Z", "WEI"];
    const hasHeader = fieldOrder.some(c => firstUpper.includes(c));
    return {
        colMap: hasHeader ? firstUpper : null,
        dataRows: parsed.slice(hasHeader ? 1 : 0),
    };
}

function fillRow(tr, cells, colMap, startCol) {
    const fieldOrder = ["WELL", "X", "Y", "Z", "WEI"];
    if (colMap) {
        colMap.forEach((col, ci) => {
            const fieldIdx = fieldOrder.indexOf(col);
            if (fieldIdx === -1) return;
            const inp = tr.cells[fieldIdx + 2]?.querySelector("input[type='text']");
            if (inp) { inp.value = cells[ci]?.trim() ?? ""; inp.dispatchEvent(new Event("input")); }
        });
    } else {
        cells.forEach((val, ci) => {
            const inp = tr.cells[startCol + ci]?.querySelector("input[type='text']");
            if (inp) { inp.value = val.trim(); inp.dispatchEvent(new Event("input")); }
        });
    }
}

document.addEventListener("paste", e => {
    const active = document.activeElement;
    if (!active?.name) return;
    e.preventDefault();

    const text = e.clipboardData.getData("text/plain");
    const lines = text.trim().split(/\r?\n/);

    if (lines.length === 1 && !/[\t;,]/.test(lines[0])) {
        active.value = lines[0];
        active.dispatchEvent(new Event("input"));
        return;
    }

    clearTable(false);

    const { colMap, dataRows } = parseClipboard(text);
    const tbody = document.getElementById("tbody");

    dataRows.forEach(cells => {
        addRow();
        const curTr = tbody.lastElementChild;
        fillRow(curTr, cells, colMap, 2);
    });

    updateRowCount();
});

document.addEventListener("htmx:afterSwap", e => {
    if (e.detail.target.id === "tbody") {
        updateRowCount();
        syncSelectAll();
    }
});

document.addEventListener("htmx:afterSettle", e => {
    if (e.detail.target.id === "result-area") {
        const el = document.getElementById("result-data");
        const dlBtn = document.getElementById("dl-btn");
        if (dlBtn) dlBtn.style.display = el ? "block" : "none";
    }
});

function downloadResult() {
    const el = document.getElementById("result-data");
    if (!el) return;

    fetch("/download", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: el.dataset.result,
    })
        .then(r => {
            const disposition = r.headers.get("Content-Disposition");
            const filename = disposition.split("filename=")[1].replace(/"/g, "");
            return r.blob().then(blob => ({ blob, filename }));
        })
        .then(({ blob, filename }) => {
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = filename;
            a.click();
            URL.revokeObjectURL(url);
        });
}

document.addEventListener("keydown", e => {
    if (e.ctrlKey && e.key === "a") {
        const active = document.activeElement;
        if (!active?.name) return;
        e.preventDefault();
        const tbody = document.getElementById("tbody");
        [...tbody.rows].forEach(tr => {
            const cb = tr.querySelector('input[type="checkbox"]');
            if (!cb) return;
            cb.checked = true;
            tr.classList.add("row-selected");
        });
        const master = document.getElementById("select-all");
        if (master) { master.checked = true; master.indeterminate = false; }
    }
});