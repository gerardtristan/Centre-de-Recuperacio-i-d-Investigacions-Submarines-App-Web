/* Zona per pujar fitxers (T-DX-117; design-system §6, «Zona per pujar fitxers», i §6.27).
   Millora progressiva d'un <input type="file"> dins d'un .zona-magnetica[data-zona-magnetica]:
   sense JavaScript, el camp funciona igual. Amb JavaScript: es pot deixar-hi el fitxer
   arrossegant-lo (.a-sobre), es mostra el nom i la mida (.te-fitxer) i, si no compleix l'«accept»
   del camp, es buida i es diu en text (.te-error). Sense animació. El servidor ho torna a
   comprovar tot (tipus pel contingut, mida, permís). */
(function () {
  "use strict";

  function mida(bytes) {
    return bytes < 1048576 ? Math.max(1, Math.round(bytes / 1024)) + " kB" : (bytes / 1048576).toFixed(1).replace(".", ",") + " MB";
  }

  function acceptat(input, fitxer) {
    const regles = (input.accept || "").split(",").map(function (r) { return r.trim().toLowerCase(); }).filter(Boolean);
    if (!regles.length) return true;
    const nom = fitxer.name.toLowerCase();
    return regles.some(function (r) {
      if (r.startsWith(".")) return nom.endsWith(r);
      if (r.endsWith("/*")) return fitxer.type.startsWith(r.slice(0, -1));
      return fitxer.type === r;
    });
  }

  function prepara(zona) {
    const input = zona.querySelector('input[type="file"]');
    if (!input) return;
    const estat = document.createElement("p");
    estat.className = "zm-resum";
    estat.setAttribute("role", "status");
    zona.append(estat);

    function mostra() {
      const fitxer = input.files && input.files[0];
      zona.classList.remove("te-fitxer", "te-error");
      estat.className = "zm-resum";
      estat.textContent = "";
      if (!fitxer) return;
      if (!acceptat(input, fitxer)) {
        input.value = "";
        zona.classList.add("te-error");
        estat.className = "zm-error";
        estat.textContent = zona.dataset.errorTipus || "";
        return;
      }
      zona.classList.add("te-fitxer");
      estat.textContent = fitxer.name + " · " + mida(fitxer.size);
    }

    input.addEventListener("change", mostra);
    ["dragenter", "dragover"].forEach(function (tipus) {
      zona.addEventListener(tipus, function (e) { e.preventDefault(); zona.classList.add("a-sobre"); });
    });
    ["dragleave", "dragend"].forEach(function (tipus) {
      zona.addEventListener(tipus, function () { zona.classList.remove("a-sobre"); });
    });
    zona.addEventListener("drop", function (e) {
      e.preventDefault();
      zona.classList.remove("a-sobre");
      if (!e.dataTransfer || !e.dataTransfer.files.length) return;
      const tria = new DataTransfer();
      tria.items.add(e.dataTransfer.files[0]);  // un fitxer per camp, com el camp mateix
      input.files = tria.files;
      mostra();
    });
  }

  document.querySelectorAll(".zona-magnetica[data-zona-magnetica]").forEach(prepara);
})();
