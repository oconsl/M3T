window.renderAll = function renderAll(variables = []) {
  renderTemplateList();
  renderTemplateForm();
  renderPreviewRecipientSelect();
  renderVariables(variables);
  renderRecipients();
};

window.loadState = async function loadState() {
  const data = await api("/api/state");
  state.templates = data.templates;
  state.recipients = data.recipients;
  state.recipientColumns = data.recipient_columns;
  state.recipientErrors = data.recipient_errors;
  if (!state.selectedTemplateId && state.templates.length) {
    state.selectedTemplateId = state.templates[0].template_id;
  }
  renderAll(data.variables);
  loadConfig();
};

function wireEvents() {
  $("templateForm").addEventListener("submit", saveTemplate);
  $("previewBtn").addEventListener("click", previewSelected);
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
  $("saveRecipientsBtn").addEventListener("click", saveRecipients);
  $("recipientSearch").addEventListener("input", renderRecipients);
  document.querySelectorAll(".tab").forEach(tab => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach(item => item.classList.remove("active"));
      tab.classList.add("active");
      $("templatesTab").classList.toggle("hidden", tab.dataset.tab !== "templates");
      $("recipientsTab").classList.toggle("hidden", tab.dataset.tab !== "recipients");
    });
  });
}

wireEvents();
loadState().then(previewSelected).catch(error => notify.error(error.message));
