// Editor de la web (T-M07-06a): arrossegar (SortableJS) i Ctrl+Z; sense JS, els botons fan el mateix.
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
})();
