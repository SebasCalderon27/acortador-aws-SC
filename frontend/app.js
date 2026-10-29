(function () {
  const API_URL = (window.APP_CONFIG && window.APP_CONFIG.API_URL || "").replace(/\/$/, "");

  const form = document.getElementById("form");
  const input = document.getElementById("url");
  const btn = document.getElementById("btn");
  const errorBox = document.getElementById("error");
  const result = document.getElementById("result");
  const shortInput = document.getElementById("short");
  const copyBtn = document.getElementById("copy");
  const openLink = document.getElementById("open");

  function showError(msg) {
    errorBox.textContent = msg;
    errorBox.hidden = false;
    result.hidden = true;
  }

  function clearError() {
    errorBox.hidden = true;
    errorBox.textContent = "";
  }

  function urlValida(value) {
    try {
      const u = new URL(value);
      return (u.protocol === "http:" || u.protocol === "https:") && u.hostname.includes(".");
    } catch (_) {
      return false;
    }
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearError();

    const original = input.value.trim();
    if (!urlValida(original)) {
      showError("La URL no es válida. Debe comenzar con http:// o https:// e incluir un dominio.");
      return;
    }

    btn.disabled = true;
    btn.textContent = "Acortando...";

    try {
      const response = await fetch(API_URL + "/shorten", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ original_url: original }),
      });

      if (!response.ok) {
        let detail = "El servidor rechazó la solicitud (código " + response.status + ").";
        try {
          const data = await response.json();
          if (response.status === 422) {
            detail = "La URL no es válida según el servidor.";
          } else if (typeof data.detail === "string") {
            detail = data.detail;
          }
        } catch (_) { /* respuesta sin JSON */ }
        showError(detail);
        return;
      }

      const data = await response.json();
      shortInput.value = data.short_url;
      openLink.href = data.short_url;
      result.hidden = false;
      copyBtn.textContent = "Copiar";
    } catch (_) {
      showError("No se pudo conectar con el backend. Verifica que la API en EC2 esté en ejecución y accesible.");
    } finally {
      btn.disabled = false;
      btn.textContent = "Acortar";
    }
  });

  copyBtn.addEventListener("click", async () => {
    const text = shortInput.value;
    try {
      await navigator.clipboard.writeText(text);
    } catch (_) {
      // Respaldo para páginas HTTP (sin API del portapapeles segura)
      shortInput.select();
      document.execCommand("copy");
    }
    copyBtn.textContent = "¡Copiado!";
    copyBtn.classList.add("done");
    setTimeout(() => {
      copyBtn.textContent = "Copiar";
      copyBtn.classList.remove("done");
    }, 1800);
  });
})();
