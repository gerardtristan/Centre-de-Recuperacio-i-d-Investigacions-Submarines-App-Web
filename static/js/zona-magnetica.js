/* Zona per pujar fitxers (T-DX-117; design-system §6, «Zona per pujar fitxers», i §6.27).
   Millora progressiva d'un <input type="file"> dins d'un .zona-magnetica[data-zona-magnetica]:
   sense JavaScript, el camp funciona igual. Amb JavaScript: es pot deixar-hi el fitxer
   arrossegant-lo (.a-sobre), es mostra el nom i la mida (.te-fitxer) i, si no compleix l'«accept»
   del camp, es buida i es diu en text (.te-error). Sense animació. El servidor ho torna a
   comprovar tot (tipus pel contingut, mida, permís).
   Amb data-vista-previa (T-DX-116, RN-M09-25): una vista prèvia de la imatge o del PDF triat, només
   al navegador: un URL blob: en memòria, que es revoca en canviar de fitxer o en sortir. El fitxer
   no s'envia fins que es prem «Desa» i no es desa enlloc (ni memòria cau ni emmagatzematge).
   Amb data-tria (T-DX-120): un botó del sistema amb aquest text («Tria un fitxer») al lloc del botó
   natiu, que surt en la llengua del navegador. El camp continua a sobre, transparent: el clic, el
   teclat i el nom accessible són els seus. */
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
    if (zona.dataset.tria) {
      const tria = document.createElement("span");
      const boto = document.createElement("span");
      tria.className = "zm-tria-fitxer";
      boto.className = "boto boto-petit";
      boto.setAttribute("aria-hidden", "true");
      boto.textContent = zona.dataset.tria;
      input.before(tria);
      tria.append(boto, input);
    }
    const estat = document.createElement("p");
    estat.className = "zm-resum";
    estat.setAttribute("role", "status");
    zona.append(estat);
    const ambVista = zona.hasAttribute("data-vista-previa");
    let url = null;

    function treuVista() {
      const vella = zona.querySelector(".zm-vista");
      if (vella) vella.remove();
      if (url) { URL.revokeObjectURL(url); url = null; }
    }

    function posaVista(fitxer) {
      const esPdf = fitxer.type === "application/pdf";
      if (!esPdf && !fitxer.type.startsWith("image/")) return;
      url = URL.createObjectURL(fitxer);
      const vista = document.createElement(esPdf ? "iframe" : "img");
      vista.className = "zm-vista";
      vista.src = url;
      if (esPdf) vista.title = zona.dataset.vistaTitol || fitxer.name;
      else vista.alt = zona.dataset.vistaTitol || fitxer.name;
      zona.append(vista);
    }
    if (ambVista) window.addEventListener("pagehide", treuVista);

    function mostra() {
      const fitxer = input.files && input.files[0];
      zona.classList.remove("te-fitxer", "te-error");
      if (ambVista) treuVista();
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
      if (ambVista) posaVista(fitxer);
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
