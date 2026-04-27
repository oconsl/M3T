window.selectedRecipientIds = function selectedRecipientIds() {
  return Array.from(document.querySelectorAll(".recipient-selected:checked"))
    .map(input => input.dataset.recipientId)
    .filter(Boolean);
};

window.selectedIndexes = function selectedIndexes() {
  return Array.from(document.querySelectorAll(".recipient-selected:checked")).map(input => Number(input.dataset.index));
};

window.dryRun = async function dryRun() {
  try {
    const ids = selectedRecipientIds();
    const data = await api("/api/dry-run", {
      method: "POST",
      body: JSON.stringify(ids.length ? { recipient_ids: ids } : { indexes: selectedIndexes() }),
    });
    const lines = data.emails.map(email => `${email.to} | ${email.message_format} | ${email.subject}`);
    if (lines.length) {
      notify.info("Dry run listo", { description: lines.join("\n"), duration: Infinity });
    } else {
      notify.warning("No hay emails seleccionados.");
    }
  } catch (error) {
    notify.error(error.message);
  }
};

window.sendSelected = async function sendSelected() {
  const ids = selectedRecipientIds();
  const indexes = selectedIndexes();
  if (!ids.length && !indexes.length) {
    notify.warning("Selecciona al menos un recipient.");
    return;
  }
  const confirmation = prompt(`Se enviaran ${ids.length || indexes.length} email(s). Escribe SEND para confirmar.`);
  if (confirmation !== "SEND") return;
  try {
    const data = await api("/api/send", {
      method: "POST",
      body: JSON.stringify(ids.length ? { recipient_ids: ids, confirm: confirmation } : { indexes, confirm: confirmation }),
    });
    notify.success(`Enviados: ${data.sent}`);
  } catch (error) {
    notify.error(error.message);
  }
};

window.connectGmail = async function connectGmail() {
  if (!confirm("Se abrira el flujo de Google en el navegador para autorizar Gmail.")) return;
  $("connectBtn").disabled = true;
  $("connectBtn").textContent = "Conectando...";
  try {
    const data = await api("/api/auth", { method: "POST", body: JSON.stringify({}) });
    notify.success(`Gmail conectado: ${data.email}`);
    await loadConfig();
  } catch (error) {
    notify.error(error.message);
  } finally {
    $("connectBtn").disabled = false;
    $("connectBtn").textContent = "Conectar Gmail";
  }
};

window.loadConfig = async function loadConfig() {
  try {
    const data = await api("/api/config");
    $("gmailStatus").textContent = data.connected ? `Gmail: ${data.email || "conectado"}` : "Gmail: sin conectar";
    $("gmailStatus").className = `notice ${data.connected ? "ok" : "warn"}`;
  } catch (error) {
    $("gmailStatus").textContent = "Gmail: sin conectar";
    $("gmailStatus").className = "notice warn";
  }
};
