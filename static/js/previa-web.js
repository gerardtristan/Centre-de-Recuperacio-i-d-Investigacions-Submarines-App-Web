// Vista prèvia de l'editor de la web (T-M07-06b): clicar un bloc el tria a l'editor (la finestra
// de fora, del mateix origen). Dins de la vista prèvia, els enllaços no naveguen.
(function () {
  "use strict";
  document.addEventListener("click", function (event) {
    var block = event.target.closest("[data-bloc]");
    if (event.target.closest("a, button")) event.preventDefault();
    if (block && window.parent !== window) {
      window.parent.postMessage({ bloc: Number(block.getAttribute("data-bloc")) }, location.origin);
    }
  });
})();
