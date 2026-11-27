// Editor de la web (T-M07-06a i 06b): arrossegar (SortableJS), Ctrl+Z, triar un bloc des de la vista
// prèvia, desat automàtic i avís d'edició simultània. Sense JS, els botons fan el mateix.
(function () {
  "use strict";
  var list = document.querySelector("[data-editor-blocs]");
  var form = document.getElementById("editor-ordre");
  if (list && form && window.Sortable && list.querySelector("[data-index]")) {
    window.Sortable.create(list, {
      handle: "[data-nansa]",
      onEnd: function (event) {
        if (event.oldIndex === event.newIndex) return;
        var order = Array.prototype.map.call(list.querySelectorAll("[data-index]"), function (item) {
          return item.getAttribute("data-index");
        });
        form.querySelector("[name=order]").value = order.join(",");
        form.submit();
      },
    });
  }
  document.addEventListener("keydown", function (event) {
    if (!(event.ctrlKey || event.metaKey) || event.key.toLowerCase() !== "z") return;
    if (event.target.closest("input, textarea, select")) return; // dins d'un camp, el del navegador
    var button = document.getElementById(event.shiftKey ? "editor-refes" : "editor-desfes");
    if (button && !button.disabled) {
      event.preventDefault();
      button.click();
    }
  });

  // Desat automàtic cada `website.autosave_seconds` (RN-M07-16) i, si no hi ha res a desar, avís
  // de qui més té la pàgina oberta (CA-M07-32). Tot ho decideix el servidor; una sola petició
  // alhora, i res es perd en sortir: abans de navegar es desa o el navegador avisa.
  var editorForm = document.querySelector("[data-desat-auto]");
  var page = document.querySelector("[data-editor-pagina]");
  var status = document.querySelector("[data-desat-estat]");
  var notice = document.querySelector("[data-avis-edicio]");
  var preview = document.querySelector("[data-vista-previa]");
  var dirty = false;
  var pending = null; // la petició en curs
  if (editorForm) {
    editorForm.addEventListener("input", function () { dirty = true; });
    editorForm.addEventListener("submit", function () { dirty = false; });
  }
  function apply(result, saving) {
    var json = result[1];
    notice.hidden = !json.others.length;
    notice.querySelector("[data-avis-noms]").textContent = json.others.join(", ");
    if (!saving) return;
    if (!result[0]) { status.textContent = json.error; return; }
    editorForm.querySelector("[name=base]").value = json.base;
    // Sense revisió nova, algú altre ha desat: les accions de la llista donaran 409 (recarregar).
    if (json.revision !== null) {
      document.querySelectorAll("[name=revision]").forEach(function (field) {
        field.value = json.revision;
      });
    }
    status.textContent = status.getAttribute("data-desat");
    var undo = document.getElementById("editor-desfes");
    undo.disabled = false;
    undo.removeAttribute("aria-disabled");
    if (preview) preview.contentWindow.location.reload();
  }
  function tick() {
    if (pending) return pending;
    var saving = dirty && editorForm;
    var data = saving ? new FormData(editorForm) : new FormData();
    if (!saving) data.append("csrfmiddlewaretoken", page.getAttribute("data-csrf"));
    dirty = false;
    pending = fetch(page.getAttribute("data-desa"), {
      method: "POST", body: data, credentials: "same-origin",
    })
      .then(function (response) {
        if ((response.headers.get("Content-Type") || "").indexOf("json") < 0) throw new Error();
        return response.json().then(function (json) { return [response.ok, json]; });
      })
      .then(function (result) { apply(result, saving); })
      .catch(function () {
        dirty = dirty || saving; // es tornarà a provar
        status.textContent = status.getAttribute("data-error");
      })
      .then(function () { pending = null; });
    return pending;
  }
  if (page) window.setInterval(tick, Number(page.getAttribute("data-interval")));
  window.addEventListener("beforeunload", function (event) {
    if (dirty || pending) { event.preventDefault(); event.returnValue = ""; }
  });

  // Clic a un bloc de la vista prèvia (previa-web.js): el tria, amb el mateix tema, després de
  // desar el que hi hagi pendent.
  window.addEventListener("message", function (event) {
    if (event.origin !== location.origin || typeof event.data.bloc !== "number") return;
    var go = function () {
      var params = new URLSearchParams(location.search);
      params.set("bloc", event.data.bloc);
      location.search = params.toString();
    };
    if (page && (dirty || pending)) tick().then(go); else go();
  });
})();
