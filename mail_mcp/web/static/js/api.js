window.state = {
  templates: [],
  recipients: [],
  recipientColumns: [],
  recipientErrors: [],
  selectedTemplateId: null,
  originalTemplateId: "",
};

window.$ = (id) => document.getElementById(id);

window.escapeHtml = function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[char]));
};

window.showMessage = function showMessage(target, messages, kind = "error") {
  const node = $(target);
  if (!messages || !messages.length) {
    node.innerHTML = "";
    return;
  }
  node.innerHTML = `<div class="notice ${kind}">${messages.map(escapeHtml).join("<br>")}</div>`;
};

window.api = async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json();
  if (!response.ok || data.ok === false) {
    throw new Error((data.errors || ["Error inesperado"]).join("\n"));
  }
  return data;
};
