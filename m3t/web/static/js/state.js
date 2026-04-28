window.renderAll = function renderAll(variables = []) {
  renderTemplateList();
  renderTemplateForm();
  renderPreviewRecipientSelect();
  renderVariables(variables, state.dynamicVariables);
  renderRecipients();
  renderDynamicValues();
};

window.loadState = async function loadState() {
  const data = await api("/api/state");
  state.templates = data.templates;
  state.recipients = data.recipients;
  state.recipientColumns = data.recipient_columns;
  state.recipientErrors = data.recipient_errors;
  state.dynamicValues = data.dynamic_values || [];
  state.dynamicErrors = data.dynamic_errors || [];
  state.dynamicVariables = data.dynamic_variables || [];
  if (!state.selectedTemplateId && state.templates.length) {
    state.selectedTemplateId = state.templates[0].template_id;
  }
  renderAll(data.variables);
  loadConfig();
};

function wireEvents() {
  $("templateForm").addEventListener("submit", saveTemplate);
  $("previewBtn").addEventListener("click", previewSelected);
  $("htmlPreviewZoomBtn").addEventListener("click", toggleHtmlPreviewZoom);
  $("formatHtmlBtn").addEventListener("click", formatHtmlEditor);
  $("previewRecipientSelect").addEventListener("change", previewSelected);
  $("refreshBtn").addEventListener("click", loadState);
  $("connectBtn").addEventListener("click", connectGmail);
  $("dryRunBtn").addEventListener("click", dryRun);
  $("sendBtn").addEventListener("click", sendSelected);
  $("newTemplateBtn").addEventListener("click", newTemplate);
  $("duplicateTemplateBtn").addEventListener("click", duplicateTemplate);
  $("deleteTemplateBtn").addEventListener("click", deleteTemplate);
  $("addRecipientBtn").addEventListener("click", addRecipient);
  $("addColumnBtn").addEventListener("click", addColumn);
  $("toggleAllRecipientsBtn").addEventListener("click", toggleAllRecipients);
  $("saveRecipientsBtn").addEventListener("click", saveRecipients);
  $("addDynamicValueBtn").addEventListener("click", addDynamicValue);
  $("saveDynamicValuesBtn").addEventListener("click", saveDynamicValues);
  $("recipientSearch").addEventListener("input", renderRecipients);
  document.querySelectorAll(".tab").forEach(tab => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach(item => item.classList.remove("active"));
      tab.classList.add("active");
      $("templatesTab").classList.toggle("hidden", tab.dataset.tab !== "templates");
      $("recipientsTab").classList.toggle("hidden", tab.dataset.tab !== "recipients");
      $("dynamicValuesTab").classList.toggle("hidden", tab.dataset.tab !== "dynamicValues");
    });
  });
}

wireEvents();
initTemplateEditors();
loadState().then(previewSelected).catch(error => notify.error(error.message));
