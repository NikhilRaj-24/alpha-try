document.addEventListener("DOMContentLoaded", () => {
    const makeSelect = document.getElementById("make");
    const modelSelect = document.getElementById("model");
    const variantSelect = document.getElementById("variant");
    const transmissionSelect = document.getElementById("transmission");
    const fuelTypeSelect = document.getElementById("fuel_type");

    const useAllRegionsCheckbox = document.getElementById("use_all_regions");
    const useFullAgeRangeCheckbox = document.getElementById("use_full_age_range");

    const submitButton = document.getElementById("submit_filter");
    const clearButton = document.getElementById("clear_filter");

    const totalRecordsElem = document.getElementById("total_records");
    const regionElem = document.getElementById("region_display");
    const ageRangeElem = document.getElementById("age_range_display");
    const resultsTableDiv = document.getElementById("results-table");

    updateDropdowns().then(loadData);

    [makeSelect, modelSelect, variantSelect, transmissionSelect, fuelTypeSelect].forEach(select => {
        select.addEventListener("change", updateDropdowns);
    });

    submitButton.addEventListener("click", () => {
        loadData();
    });

    clearButton.addEventListener("click", () => {
        makeSelect.value = "All";
        modelSelect.value = "All";
        variantSelect.value = "All";
        transmissionSelect.value = "All";
        fuelTypeSelect.value = "All";
        useAllRegionsCheckbox.checked = false;
        useFullAgeRangeCheckbox.checked = false;
        updateDropdowns().then(loadData);
    });

    function getFilterPayload() {
        return {
            Make: makeSelect.value || "All",
            Model: modelSelect.value || "All",
            Variant: variantSelect.value || "All",
            Transmission: transmissionSelect.value || "All",
            FuelType: fuelTypeSelect.value || "All",
            UseAllRegions: useAllRegionsCheckbox.checked,
            UseFullAgeRange: useFullAgeRangeCheckbox.checked
        };
    }

    function updateDropdowns() {
        const payload = getFilterPayload();
        return fetch("/options", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(payload)
        })
        .then(res => res.json())
        .then(data => {
            populateDropdown(makeSelect, data.Make);
            populateDropdown(modelSelect, data.Model);
            populateDropdown(variantSelect, data.Variant);
            populateDropdown(transmissionSelect, data.Transmission);
            populateDropdown(fuelTypeSelect, data.FuelType);
        });
    }

    function loadData() {
        const payload = getFilterPayload();
        fetch("/filter", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(payload)
        })
        .then(response => response.json())
        .then(data => {
            totalRecordsElem.textContent = data.total_records;
            regionElem.textContent = data.region;
            ageRangeElem.textContent = data.age_range;
            renderTable(data.records);
        });
    }

    function populateDropdown(selectElem, options) {
        const currentValue = selectElem.value;
        selectElem.innerHTML = "";
        options.forEach(opt => {
            const option = document.createElement("option");
            option.value = opt;
            option.textContent = opt;
            selectElem.appendChild(option);
        });
        if (options.includes(currentValue)) {
            selectElem.value = currentValue;
        }
    }

    function renderTable(records) {
        resultsTableDiv.innerHTML = "";
        if (records.length === 0) {
            const noData = document.createElement("div");
            noData.textContent = "No records found.";
            noData.classList.add("no-data");
            resultsTableDiv.appendChild(noData);
            return;
        }

        const cols = ["Make", "Model", "Variant", "Transmission", "Fuel Type",
                      "Price_numeric", "Distance_numeric", "City", "Age"];

        const table = document.createElement("table");
        table.classList.add("table", "table-striped", "table-hover", "table-bordered", "align-middle");

        const thead = document.createElement("thead");
        const headerRow = document.createElement("tr");
        cols.forEach(col => {
            const th = document.createElement("th");
            th.textContent = col;
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        table.appendChild(thead);

        const tbody = document.createElement("tbody");
        records.forEach(record => {
            const tr = document.createElement("tr");
            cols.forEach(col => {
                const td = document.createElement("td");
                td.textContent = record[col];
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
        table.appendChild(tbody);

        resultsTableDiv.appendChild(table);
    }
});
