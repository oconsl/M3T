window.selectedRecipientIds = function selectedRecipientIds() {
  return Array.from(document.querySelectorAll(".recipient-selected:checked"))
    .map(input => input.dataset.recipientId)
    .filter(Boolean);
};

window.selectedIndexes = function selectedIndexes() {
  return Array.from(document.querySelectorAll(".recipient-selected:checked")).map(input => Number(input.dataset.index));
};

function selectedSendTargets() {
  return Array.from(document.querySelectorAll(".recipient-selected:checked")).map(input => {
    const index = Number(input.dataset.index);
    const recipient = state.recipients[index] || {};
    return {
      index,
      recipientId: input.dataset.recipientId || "",
      email: recipient.email || `Fila ${index + 1}`,
    };
  });
}

function wait(milliseconds) {
  return new Promise(resolve => window.setTimeout(resolve, milliseconds));
}

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
  const targets = selectedSendTargets();
  if (!targets.length) {
    notify.warning("Selecciona al menos un recipient.");
    return;
  }
  const confirmation = await confirmSend(targets.length);
  if (confirmation !== "SEND") return;
  const sendBtn = $("sendBtn");
  sendBtn.disabled = true;
  try {
    for (const [index, target] of targets.entries()) {
      notify.message(`Enviando ${index + 1}/${targets.length}`, {
        description: target.email,
        duration: 12000,
      });
      await api("/api/send", {
        method: "POST",
        body: JSON.stringify(
          target.recipientId
            ? { recipient_ids: [target.recipientId], confirm: confirmation }
            : { indexes: [target.index], confirm: confirmation }
        ),
      });
      if (index < targets.length - 1) {
        await wait(10000);
      }
    }
    notify.success(`Enviados: ${targets.length}`);
  } catch (error) {
    notify.error(error.message);
  } finally {
    sendBtn.disabled = false;
  }
};

window.confirmSend = function confirmSend(count) {
  const modal = $("sendConfirmModal");
  const input = $("sendConfirmInput");
  const submit = $("sendConfirmSubmitBtn");
  const cancel = $("sendConfirmCancelBtn");
  const close = $("sendConfirmCloseBtn");
  const description = $("sendConfirmDescription");
  const error = $("sendConfirmError");
  const previousFocus = document.activeElement;

  return new Promise((resolve) => {
    function setOpen(isOpen) {
      modal.classList.toggle("hidden", !isOpen);
      document.body.classList.toggle("modal-open", isOpen);
    }

    function cleanup(value = null) {
      setOpen(false);
      input.value = "";
      submit.disabled = true;
      error.textContent = "";
      input.removeEventListener("input", handleInput);
      input.removeEventListener("keydown", handleInputKeydown);
      submit.removeEventListener("click", handleSubmit);
      cancel.removeEventListener("click", handleCancel);
      close.removeEventListener("click", handleCancel);
      modal.removeEventListener("click", handleBackdrop);
      document.removeEventListener("keydown", handleDocumentKeydown);
      if (previousFocus && previousFocus.focus) previousFocus.focus();
      resolve(value);
    }

    function handleInput() {
      const isConfirmed = input.value === "SEND";
      submit.disabled = !isConfirmed;
      error.textContent = input.value && !isConfirmed ? "La confirmacion debe coincidir exactamente con SEND." : "";
    }

    function handleInputKeydown(event) {
      if (event.key === "Enter" && input.value === "SEND") {
        event.preventDefault();
        cleanup("SEND");
      }
    }

    function handleSubmit() {
      if (input.value === "SEND") cleanup("SEND");
    }

    function handleCancel() {
      cleanup(null);
    }

    function handleBackdrop(event) {
      if (event.target === modal) cleanup(null);
    }

    function handleDocumentKeydown(event) {
      if (event.key === "Escape") {
        cleanup(null);
      }
    }

    description.textContent = `Se enviaran ${count} email(s). Esta accion usa Gmail y no se puede deshacer desde M3T.`;
    input.addEventListener("input", handleInput);
    input.addEventListener("keydown", handleInputKeydown);
    submit.addEventListener("click", handleSubmit);
    cancel.addEventListener("click", handleCancel);
    close.addEventListener("click", handleCancel);
    modal.addEventListener("click", handleBackdrop);
    document.addEventListener("keydown", handleDocumentKeydown);
    setOpen(true);
    input.focus();
  });
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
