window.renderDynamicValues = function renderDynamicValues() {
  $("dynamicValuesBody").innerHTML = state.dynamicValues.map((row, index) => {
    const errors = state.dynamicErrors[index] || [];
    return `
      <tr data-index="${index}">
        <td><input class="dynamic-value-input" data-index="${index}" data-column="dynamic_key" value="${escapeHtml(row.dynamic_key || "")}"></td>
        <td><input class="dynamic-value-input dynamic-value-text" data-index="${index}" data-column="value" value="${escapeHtml(row.value || "")}"></td>
        <td>
          <select class="dynamic-value-input" data-index="${index}" data-column="enabled">
            <option value="yes" ${row.enabled === "yes" ? "selected" : ""}>yes</option>
            <option value="no" ${row.enabled !== "yes" ? "selected" : ""}>no</option>
          </select>
        </td>
        <td>${errors.length ? `<div class="notice error">${errors.map(escapeHtml).join("<br>")}</div>` : `<span class="notice ok">OK</span>`}</td>
        <td><button class="danger delete-dynamic-value" data-index="${index}">Borrar</button></td>
      </tr>
    `;
  }).join("");

  document.querySelectorAll(".dynamic-value-input").forEach(input => {
    const syncDynamicValueInput = () => {
      state.dynamicValues[Number(input.dataset.index)][input.dataset.column] = input.value;
    };
    input.addEventListener("input", syncDynamicValueInput);
    input.addEventListener("change", syncDynamicValueInput);
  });
  document.querySelectorAll(".delete-dynamic-value").forEach(button => {
    button.addEventListener("click", () => {
      state.dynamicValues.splice(Number(button.dataset.index), 1);
      state.dynamicErrors.splice(Number(button.dataset.index), 1);
      renderDynamicValues();
    });
  });
};

window.addDynamicValue = function addDynamicValue() {
  state.dynamicValues.push({ dynamic_key: "", value: "", enabled: "yes" });
  state.dynamicErrors.push([]);
  renderDynamicValues();
};

window.saveDynamicValues = async function saveDynamicValues() {
  try {
    await api("/api/dynamic-values", {
      method: "POST",
      body: JSON.stringify({ rows: state.dynamicValues }),
    });
    showMessage("dynamicValueMessages", ["Dynamic values guardados."], "ok");
    await loadState();
  } catch (error) {
    showMessage("dynamicValueMessages", error.message.split("\n"), "error");
  }
};
