(function notifications() {
  const fallbackToasts = new Map();
  let fallbackRoot = null;
  let sonnerPromise = null;
  let sonnerToast = null;

  function ensureFallbackRoot() {
    if (fallbackRoot) return fallbackRoot;
    fallbackRoot = document.createElement("div");
    fallbackRoot.className = "toast-region";
    fallbackRoot.setAttribute("aria-live", "polite");
    fallbackRoot.setAttribute("aria-atomic", "false");
    document.body.appendChild(fallbackRoot);
    return fallbackRoot;
  }

  function normalizeMessage(message) {
    return String(message || "Error inesperado");
  }

  function fallback(type, message, options = {}) {
    const root = ensureFallbackRoot();
    const id = crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`;
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.setAttribute("role", type === "error" ? "alert" : "status");

    const title = document.createElement("strong");
    title.textContent = normalizeMessage(message);
    toast.appendChild(title);

    if (options.description) {
      const description = document.createElement("p");
      description.textContent = String(options.description);
      toast.appendChild(description);
    }

    const close = document.createElement("button");
    close.type = "button";
    close.className = "toast-close";
    close.setAttribute("aria-label", "Cerrar notificacion");
    close.textContent = "x";
    close.addEventListener("click", () => dismissFallback(id));
    toast.appendChild(close);

    root.appendChild(toast);
    fallbackToasts.set(id, toast);

    const duration = options.duration === Infinity ? Infinity : options.duration || 5000;
    if (duration !== Infinity) {
      window.setTimeout(() => dismissFallback(id), duration);
    }
  }

  function dismissFallback(id) {
    const toast = fallbackToasts.get(id);
    if (!toast) return;
    toast.classList.add("toast-hiding");
    window.setTimeout(() => {
      toast.remove();
      fallbackToasts.delete(id);
    }, 180);
  }

  function loadSonner() {
    if (sonnerToast) return Promise.resolve(sonnerToast);
    if (!sonnerPromise) {
      sonnerPromise = import("https://cdn.jsdelivr.net/npm/@numer/sonner@1.2.3/+esm")
        .then((module) => {
          sonnerToast = module.default || module.toast || module;
          if (sonnerToast.config) {
            sonnerToast.config({
              position: "top-right",
              theme: "light",
              richColors: true,
            });
          }
          return sonnerToast;
        });
    }
    return sonnerPromise;
  }

  function show(type, message, options = {}) {
    const normalized = normalizeMessage(message);
    loadSonner()
      .then((toast) => {
        const trigger = toast[type] || toast;
        trigger.call(toast, normalized, options);
      })
      .catch(() => fallback(type, normalized, options));
  }

  window.notify = {
    success: (message, options) => show("success", message, options),
    error: (message, options) => show("error", message, { duration: 7000, ...options }),
    info: (message, options) => show("info", message, options),
    warning: (message, options) => show("warning", message, options),
    message: (message, options) => show("message", message, options),
  };

  window.addEventListener("DOMContentLoaded", () => {
    loadSonner().catch(() => {});
  });
}());
