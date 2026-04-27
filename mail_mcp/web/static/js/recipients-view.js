window.renderPreviewRecipientSelect = function renderPreviewRecipientSelect() {
  $("previewRecipientSelect").innerHTML = state.recipients.map((recipient, index) => `
    <option value="${index}">${escapeHtml(recipient.email || `Fila ${index + 1}`)}</option>
  `).join("");
};

window.renderRecipients = function renderRecipients() {
  const query = $("recipientSearch").value.trim().toLowerCase();
  $("recipientsHead").innerHTML = `<tr><th>Usar</th>${state.recipientColumns.map(column => `<th>${escapeHtml(column)}</th>`).join("")}<th>Estado</th><th></th></tr>`;
  $("recipientsBody").innerHTML = state.recipients.map((row, index) => {
    const blob = Object.values(row).join(" ").toLowerCase();
    if (query && !blob.includes(query)) return "";
    const errors = state.recipientErrors[index] || [];
    return `
      <tr data-index="${index}">
        <td><input type="checkbox" class="recipient-selected" data-index="${index}" data-recipient-id="${escapeHtml(row.recipient_id || "")}" ${row.send === "yes" ? "checked" : ""}></td>
        ${state.recipientColumns.map(column => `<td>${recipientCell(column, row[column] || "", index)}</td>`).join("")}
        <td>${errors.length ? `<div class="notice error">${errors.map(escapeHtml).join("<br>")}</div>` : `<span class="notice ok">OK</span>`}</td>
        <td><button class="danger delete-recipient" data-index="${index}">Borrar</button></td>
      </tr>
    `;
  }).join("");

  document.querySelectorAll(".recipient-input").forEach(input => {
    const syncRecipientInput = () => {
      state.recipients[Number(input.dataset.index)][input.dataset.column] = input.value;
    };
    input.addEventListener("input", syncRecipientInput);
    input.addEventListener("change", syncRecipientInput);
  });
  document.querySelectorAll(".recipient-selected").forEach(input => {
    input.addEventListener("change", () => {
      state.recipients[Number(input.dataset.index)].send = input.checked ? "yes" : "no";
      renderRecipients();
    });
  });
  document.querySelectorAll(".delete-recipient").forEach(button => {
    button.addEventListener("click", () => {
      state.recipients.splice(Number(button.dataset.index), 1);
      state.recipientErrors.splice(Number(button.dataset.index), 1);
      renderRecipients();
    });
  });
};

window.recipientCell = function recipientCell(column, value, index) {
  if (column === "template_id") {
    return `<select class="recipient-input" data-index="${index}" data-column="${escapeHtml(column)}">
      ${state.templates.map(template => `<option value="${escapeHtml(template.template_id)}" ${template.template_id === value ? "selected" : ""}>${escapeHtml(template.template_id)}</option>`).join("")}
    </select>`;
  }
  if (column === "send") {
    return `<select class="recipient-input" data-index="${index}" data-column="send">
      <option value="yes" ${value === "yes" ? "selected" : ""}>yes</option>
      <option value="no" ${value !== "yes" ? "selected" : ""}>no</option>
    </select>`;
  }
  if (column === "message_format") {
    return `<select class="recipient-input" data-index="${index}" data-column="message_format">
      <option value="html" ${value !== "plain" ? "selected" : ""}>html</option>
      <option value="plain" ${value === "plain" ? "selected" : ""}>plain</option>
    </select>`;
  }
  return `<input class="recipient-input" data-index="${index}" data-column="${escapeHtml(column)}" value="${escapeHtml(value)}">`;
};

window.saveRecipients = async function saveRecipients() {
  try {
    await api("/api/recipients", {
      method: "POST",
      body: JSON.stringify({ columns: state.recipientColumns, rows: state.recipients }),
    });
    showMessage("recipientMessages", ["Recipients guardados."], "ok");
    await loadState();
  } catch (error) {
    showMessage("recipientMessages", error.message.split("\n"), "error");
  }
};

window.addRecipient = function addRecipient() {
  const row = {};
  state.recipientColumns.forEach(column => row[column] = "");
  row.recipient_id = crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`;
  row.send = "yes";
  row.template_id = state.templates[0]?.template_id || "";
  row.message_format = "html";
  state.recipients.push(row);
  state.recipientErrors.push([]);
  renderRecipients();
};

window.addColumn = function addColumn() {
  const name = prompt("Nombre de la columna:");
  if (!name || state.recipientColumns.includes(name) || name === "recipient_id") return;
  state.recipientColumns.push(name);
  state.recipients.forEach(row => row[name] = "");
  renderRecipients();
};
