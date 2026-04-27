window.renderTemplateList = function renderTemplateList() {
  $("templateList").innerHTML = state.templates.map(template => `
    <button class="template-item ${template.template_id === state.selectedTemplateId ? "active" : ""}" data-template-id="${escapeHtml(template.template_id)}">
      <strong>${escapeHtml(template.template_id)}</strong>
      <div class="muted">${escapeHtml(template.subject)}</div>
      ${template.errors.length ? `<div class="muted" style="color: var(--danger);">${template.errors.length} error(es)</div>` : ""}
    </button>
  `).join("");
  document.querySelectorAll(".template-item").forEach(button => {
    button.addEventListener("click", () => {
      state.selectedTemplateId = button.dataset.templateId;
      renderTemplateList();
      renderTemplateForm();
      previewSelected();
    });
  });
};

window.selectedTemplate = function selectedTemplate() {
  return state.templates.find(template => template.template_id === state.selectedTemplateId) || null;
};

window.renderTemplateForm = function renderTemplateForm() {
  const template = selectedTemplate();
  state.originalTemplateId = template ? template.template_id : "";
  $("templateIdInput").value = template ? template.template_id : "";
  $("subjectInput").value = template ? template.subject : "";
  $("bodyTextInput").value = template ? template.body_text : "";
  $("bodyHtmlInput").value = template ? template.body_html : "";
  showMessage("templateMessages", template && template.errors ? template.errors : [], "error");
};

window.renderVariables = function renderVariables(variables) {
  $("variablesPanel").innerHTML = variables.map(variable => `<span class="pill">{${escapeHtml(variable)}}</span>`).join("");
};

window.saveTemplate = async function saveTemplate(event) {
  event.preventDefault();
  try {
    await api("/api/templates", {
      method: "POST",
      body: JSON.stringify({
        original_id: state.originalTemplateId,
        template_id: $("templateIdInput").value,
        subject: $("subjectInput").value,
        body_text: $("bodyTextInput").value,
        body_html: $("bodyHtmlInput").value,
      }),
    });
    state.selectedTemplateId = $("templateIdInput").value.trim();
    showMessage("templateMessages", ["Template guardado."], "ok");
    await loadState();
  } catch (error) {
    showMessage("templateMessages", error.message.split("\n"), "error");
  }
};

window.newTemplate = function newTemplate() {
  state.selectedTemplateId = null;
  state.originalTemplateId = "";
  $("templateIdInput").value = "";
  $("subjectInput").value = "";
  $("bodyTextInput").value = "";
  $("bodyHtmlInput").value = "";
  showMessage("templateMessages", [], "ok");
};

window.duplicateTemplate = async function duplicateTemplate() {
  const source = selectedTemplate();
  if (!source) return;
  const newId = prompt("Nuevo template_id:", `${source.template_id}-copy`);
  if (!newId) return;
  try {
    await api("/api/templates/duplicate", {
      method: "POST",
      body: JSON.stringify({ source_id: source.template_id, new_id: newId }),
    });
    state.selectedTemplateId = newId;
    await loadState();
  } catch (error) {
    showMessage("templateMessages", error.message.split("\n"), "error");
  }
};

window.deleteTemplate = async function deleteTemplate() {
  const source = selectedTemplate();
  if (!source || !confirm(`Borrar template ${source.template_id}?`)) return;
  try {
    await api(`/api/templates/${encodeURIComponent(source.template_id)}`, { method: "DELETE" });
    state.selectedTemplateId = null;
    await loadState();
  } catch (error) {
    showMessage("templateMessages", error.message.split("\n"), "error");
  }
};
