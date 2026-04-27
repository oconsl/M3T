window.previewSelected = async function previewSelected() {
  const templateId = $("templateIdInput").value.trim() || state.selectedTemplateId;
  if (!templateId) return;
  try {
    const recipientIndex = Number($("previewRecipientSelect").value || 0);
    const messageFormat = state.recipients[recipientIndex]?.message_format || "html";
    const data = await api("/api/preview", {
      method: "POST",
      body: JSON.stringify({
        template_id: templateId,
        recipient_index: recipientIndex,
        message_format: messageFormat,
        subject: $("subjectInput").value,
        body_text: $("bodyTextInput").value,
        body_html: $("bodyHtmlInput").value,
      }),
    });
    $("previewSubject").value = data.subject;
    $("previewText").textContent = data.body_text;
    $("previewHtml").srcdoc = data.body_html || "<body></body>";
    showMessage("previewWarnings", [
      `Version seleccionada: ${data.message_format}`,
      ...data.missing_variables.map(variable => `Variable sin valor: {${variable}}`),
    ], "warn");
  } catch (error) {
    showMessage("previewWarnings", error.message.split("\n"), "error");
  }
};
