const COLS = ["WELL", "X", "Y", "Z", "WEI"];

document.addEventListener("DOMContentLoaded", async () => {
    const prefs = await fetch("/prefs").then(r => r.json());
    document.getElementById("decimal").value = prefs.decimal;
    document.getElementById("thousands").value = prefs.thousands;
    document.getElementById("csvsep").value = prefs.csvsep;
    document.documentElement.dataset.theme = prefs.theme;
    updateThemeBtn(prefs.theme);
    validateSeparators();
});

document.getElementById("decimal").addEventListener("change", e => {
    savePrefs({ decimal: e.target.value });
    setTimeout(validateSeparators, 0);
});

document.getElementById("thousands").addEventListener("change", e => {
    savePrefs({ thousands: e.target.value });
    setTimeout(validateSeparators, 0);
});

document.getElementById("csvsep").addEventListener("change", e => {
    savePrefs({ csvsep: e.target.value });
    setTimeout(validateSeparators, 0);
});

function savePrefs(patch) {
    fetch("/prefs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(patch),
    });
}


function toggleTheme() {
    const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    updateThemeBtn(next);
    savePrefs({ theme: next });
}

async function openImportDialog() {
    const res = await fetch("/open-file-dialog").then(r => r.json());
    view.page().runJavaScript(`handleOpenFile(${JSON.stringify(res.dir)})`);
}

async function triggerImportFromPath(path) {
    const res = await fetch("/read-file", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path }),
    }).then(r => r.json());

    if (res.error) { showErr(res.error); return; }

    const sep = document.getElementById("csvsep").value;
    const thousands = document.getElementById("thousands").value;
    const decimal = document.getElementById("decimal").value;

    const blob = new Blob([res.content], { type: "text/csv" });
    const file = new File([blob], path.split("/").pop(), { type: "text/csv" });
    const formData = new FormData();
    formData.append("file", file);
    formData.append("sep", sep);
    formData.append("thousands", thousands);
    formData.append("decimal", decimal);

    document.getElementById("tbody").innerHTML = "";
    updateRowCount();

    htmx.ajax("POST", "/import-csv", {
        target: "#tbody",
        swap: "innerHTML",
        values: formData,
    });
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

    const tableScroll = document.querySelector(".table-scroll");
    if (tableScroll) {
        tableScroll.scrollTop = tableScroll.scrollHeight;
    }
}

function deleteSelected() {
    const tbody = document.getElementById("tbody");
    const selected = [...tbody.rows].filter(tr =>
        tr.querySelector('input[type="checkbox"]')?.checked
    );
    if (!selected.length) return;

    const hasData = selected.some(tr =>
        ["well", "x", "y", "z", "wei"].some(name =>
            tr.querySelector(`input[name^="${name}_"]`)?.value.trim()
        )
    );

    if (!hasData) {
        selected.forEach(tr => tr.remove());
        reindex();
        updateRowCount();
        syncSelectAll();
        return;
    }

    const body = document.getElementById("modal-body");
    body.innerHTML = "";
    selected.forEach(tr => {
        const well = tr.querySelector('input[name^="well_"]')?.value.trim();
        const x = tr.querySelector('input[name^="x_"]')?.value.trim();
        const y = tr.querySelector('input[name^="y_"]')?.value.trim();
        const z = tr.querySelector('input[name^="z_"]')?.value.trim();
        const wei = tr.querySelector('input[name^="wei_"]')?.value.trim();
        const values = [well, x, y, z, wei];
        const span = document.createElement("span");
        span.textContent = values.some(v => v)
            ? values.map(v => v || "—").join("  ·  ")
            : "(empty)";
        body.appendChild(span);
    });

    document.getElementById("modal-overlay").classList.add("on");
}

function confirmDelete() {
    const tbody = document.getElementById("tbody");
    [...tbody.rows]
        .filter(tr => tr.querySelector('input[type="checkbox"]')?.checked)
        .forEach(tr => tr.remove());
    reindex();
    updateRowCount();
    syncSelectAll();
    closeModal();
}

function closeModal() {
    document.getElementById("modal-overlay").classList.remove("on");
}

document.getElementById("modal-overlay").addEventListener("click", e => {
    if (e.target === e.currentTarget) closeModal();
});

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

function copyResult() {
    const el = document.getElementById("result-data");
    if (!el) return;

    const result = JSON.parse(el.dataset.result);
    const csv = "PRODUCER,INJECTOR\n" +
        result.map(([prod, inj]) => `${prod},${inj}`).join("\n");

    const textarea = document.createElement("textarea");
    textarea.value = csv;
    textarea.style.position = "fixed";
    textarea.style.opacity = "0";
    document.body.appendChild(textarea);
    textarea.focus();
    textarea.select();
    document.execCommand("copy");
    document.body.removeChild(textarea);

    const btn = document.querySelector(".copy-btn");
    btn.classList.add("copied");
    btn.innerHTML = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" stroke-width="2" stroke-linecap="round">
    <polyline points="20 6 9 17 4 12"/>
  </svg>`;
    setTimeout(() => {
        btn.classList.remove("copied");
        btn.innerHTML = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" stroke-width="2" stroke-linecap="round">
      <rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
    </svg>`;
    }, 2000);
}

function showToast(msg) {
    const t = document.getElementById("toast");
    t.textContent = msg;
    t.classList.add("on");
    clearTimeout(t._timer);
    t._timer = setTimeout(() => t.classList.remove("on"), 2400);
}

document.getElementById("import-csv").addEventListener("change", function () {
    document.getElementById("tbody").innerHTML = "";
    document.getElementById("result-area").innerHTML = "";
    document.getElementById("dl-btn").style.display = "none";
    updateRowCount();
    syncImportMeta();
    setTimeout(() => {
        htmx.trigger("#import-form", "submit");
        this.value = "";
    }, 50);
});

function validateSeparators() {
    const decimal = document.getElementById("decimal").value;
    const thousands = document.getElementById("thousands").value;
    const csvsep = document.getElementById("csvsep").value;

    document.querySelectorAll("#thousands option").forEach(opt => {
        opt.disabled = [decimal, csvsep].includes(opt.value) && opt.value
    });

    document.querySelectorAll("#decimal option").forEach(opt => {
        opt.disabled = [thousands, csvsep].includes(opt.value)
    });

    document.querySelectorAll("#csvsep option").forEach(opt => {
        opt.disabled = opt.value === decimal || (thousands && opt.value === thousands);
    });
}