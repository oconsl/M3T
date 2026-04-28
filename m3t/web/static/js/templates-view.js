const templateEditors = {
  text: null,
  html: null,
  monacoReady: false,
  completionDisposables: [],
};

function placeholderSuggestions(monaco, range) {
  const dataVariables = (state.recipientColumns || [])
    .concat(["from_name"])
    .filter((value, index, values) => value && values.indexOf(value) === index)
    .map(variable => ({
      label: `{${variable}}`,
      kind: monaco.languages.CompletionItemKind.Variable,
      insertText: `{${variable}}`,
      detail: "Recipient value",
      range,
    }));
  const dynamicVariables = (state.dynamicVariables || []).map(variable => ({
    label: `{dynamic.${variable}}`,
    kind: monaco.languages.CompletionItemKind.Value,
    insertText: `{dynamic.${variable}}`,
    detail: "Dynamic value",
    range,
  }));
  return [...dataVariables, ...dynamicVariables];
}

function registerTemplateCompletion(monaco) {
  templateEditors.completionDisposables.forEach(disposable => disposable.dispose());
  templateEditors.completionDisposables = ["m3t-template", "html"].map(language => monaco.languages.registerCompletionItemProvider(language, {
    triggerCharacters: ["{", ".", "_"],
    provideCompletionItems(model, position) {
      const linePrefix = model.getLineContent(position.lineNumber).slice(0, position.column - 1);
      const placeholderMatch = linePrefix.match(/\{[A-Za-z0-9_.]*$/);
      const word = model.getWordUntilPosition(position);
      const range = {
        startLineNumber: position.lineNumber,
        endLineNumber: position.lineNumber,
        startColumn: placeholderMatch ? position.column - placeholderMatch[0].length : word.startColumn,
        endColumn: word.endColumn,
      };
      return { suggestions: placeholderSuggestions(monaco, range) };
    },
  }));
}

function configureTemplateLanguage(monaco) {
  const hasTemplateLanguage = monaco.languages.getLanguages().some(language => language.id === "m3t-template");
  if (!hasTemplateLanguage) {
    monaco.languages.register({ id: "m3t-template" });
    monaco.languages.setMonarchTokensProvider("m3t-template", {
      tokenizer: {
        root: [
          [/\{dynamic\.[A-Za-z_][A-Za-z0-9_]*\}/, "variable.predefined"],
          [/\{[A-Za-z_][A-Za-z0-9_]*\}/, "variable"],
        ],
      },
    });
  }
  monaco.editor.defineTheme("m3t-light", {
    base: "vs",
    inherit: true,
    rules: [
      { token: "variable", foreground: "3538cd", fontStyle: "bold" },
      { token: "variable.predefined", foreground: "027a48", fontStyle: "bold" },
    ],
    colors: {
      "editor.lineHighlightBackground": "#f8fafc",
      "editorGutter.background": "#ffffff",
    },
  });
  registerTemplateCompletion(monaco);
}

function createTemplateEditor(monaco, hostId, textareaId, language) {
  const textarea = $(textareaId);
  const host = $(hostId);
  const editor = monaco.editor.create(host, {
    value: textarea.value,
    language,
    theme: "m3t-light",
    automaticLayout: true,
    minimap: { enabled: false },
    scrollBeyondLastLine: false,
    wordWrap: "on",
    tabSize: 2,
    fontSize: 13,
    lineHeight: 20,
    padding: { top: 10, bottom: 10 },
    quickSuggestions: { other: true, comments: true, strings: true },
    suggestOnTriggerCharacters: true,
  });
  editor.onDidChangeModelContent(() => {
    textarea.value = editor.getValue();
  });
  host.addEventListener("click", () => editor.focus());
  textarea.closest(".code-editor-field").classList.add("is-monaco-ready");
  host.setAttribute("aria-hidden", "false");
  return editor;
}

window.initTemplateEditors = function initTemplateEditors() {
  if (!window.require) return;
  window.require.config({ paths: { vs: "https://cdn.jsdelivr.net/npm/monaco-editor@0.49.0/min/vs" } });
  window.require(["vs/editor/editor.main"], () => {
    if (!window.monaco || templateEditors.monacoReady) return;
    configureTemplateLanguage(window.monaco);
    templateEditors.text = createTemplateEditor(window.monaco, "bodyTextEditor", "bodyTextInput", "m3t-template");
    templateEditors.html = createTemplateEditor(window.monaco, "bodyHtmlEditor", "bodyHtmlInput", "html");
    templateEditors.monacoReady = true;
    setTemplateEditorValues({
      body_text: $("bodyTextInput").value,
      body_html: $("bodyHtmlInput").value,
    });
  });
};

window.getTemplateEditorValues = function getTemplateEditorValues() {
  return {
    body_text: templateEditors.text ? templateEditors.text.getValue() : $("bodyTextInput").value,
    body_html: templateEditors.html ? templateEditors.html.getValue() : $("bodyHtmlInput").value,
  };
};

window.setTemplateEditorValues = function setTemplateEditorValues(values) {
  const bodyText = values.body_text || "";
  const bodyHtml = values.body_html || "";
  $("bodyTextInput").value = bodyText;
  $("bodyHtmlInput").value = bodyHtml;
  if (templateEditors.text && templateEditors.text.getValue() !== bodyText) {
    templateEditors.text.setValue(bodyText);
  }
  if (templateEditors.html && templateEditors.html.getValue() !== bodyHtml) {
    templateEditors.html.setValue(bodyHtml);
  }
};

window.formatHtmlEditor = function formatHtmlEditor() {
  if (!templateEditors.html) return;
  templateEditors.html.getAction("editor.action.formatDocument").run();
};

window.toggleHtmlPreviewZoom = function toggleHtmlPreviewZoom() {
  const panel = $("previewPanel");
  const button = $("htmlPreviewZoomBtn");
  const nextIsExpanded = !panel.classList.contains("is-html-expanded");
  panel.classList.toggle("is-html-expanded", nextIsExpanded);
  button.textContent = nextIsExpanded ? "Minimizar HTML" : "Maximizar HTML";
  button.setAttribute("aria-expanded", String(nextIsExpanded));
  if (nextIsExpanded) previewSelected();
};

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
  setTemplateEditorValues({
    body_text: template ? template.body_text : "",
    body_html: template ? template.body_html : "",
  });
  showMessage("templateMessages", template && template.errors ? template.errors : [], "error");
};

window.renderVariables = function renderVariables(variables, dynamicVariables = []) {
  const dataPills = variables.map(variable => `<span class="pill">{${escapeHtml(variable)}}</span>`);
  const dynamicPills = dynamicVariables.map(variable => `<span class="pill dynamic-pill">{dynamic.${escapeHtml(variable)}}</span>`);
  $("variablesPanel").innerHTML = [...dataPills, ...dynamicPills].join("");
};

window.saveTemplate = async function saveTemplate(event) {
  event.preventDefault();
  const editorValues = getTemplateEditorValues();
  try {
    await api("/api/templates", {
      method: "POST",
      body: JSON.stringify({
        original_id: state.originalTemplateId,
        template_id: $("templateIdInput").value,
        subject: $("subjectInput").value,
        body_text: editorValues.body_text,
        body_html: editorValues.body_html,
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
  setTemplateEditorValues({ body_text: "", body_html: "" });
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
