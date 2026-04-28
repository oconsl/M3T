window.previewSelected = async function previewSelected() {
  const templateId = $("templateIdInput").value.trim() || state.selectedTemplateId;
  if (!templateId) return;
  try {
    const recipientIndex = Number($("previewRecipientSelect").value || 0);
    const messageFormat = state.recipients[recipientIndex]?.message_format || "html";
    const editorValues = getTemplateEditorValues();
    const data = await api("/api/preview", {
      method: "POST",
      body: JSON.stringify({
        template_id: templateId,
        recipient_index: recipientIndex,
        message_format: messageFormat,
        subject: $("subjectInput").value,
        body_text: editorValues.body_text,
        body_html: editorValues.body_html,
      }),
    });
    $("previewSubject").value = data.subject;
    $("previewText").textContent = data.body_text;
    $("previewHtml").srcdoc = data.body_html || "<body></body>";
    showMessage("previewWarnings", [
      `Version seleccionada: ${data.message_format}`,
      ...data.missing_variables.map(variable => `Variable sin valor: {${variable}}`),
      ...data.missing_dynamic_values.map(variable => `Dynamic sin opciones activas: {dynamic.${variable}}`),
    ], "warn");
  } catch (error) {
    showMessage("previewWarnings", error.message.split("\n"), "error");
  }
};
