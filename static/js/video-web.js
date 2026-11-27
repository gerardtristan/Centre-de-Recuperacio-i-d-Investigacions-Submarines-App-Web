// Bloc de vídeo de YouTube (T-M07-23, RN-M07-09): fins que el visitant prem el botó no es demana
// res a Google; llavors es crea l'iframe de youtube-nocookie.com (l'adreça ve del servidor).
(function () {
  "use strict";
  if (window.criVideoWeb) return; // un sol cop encara que hi hagi diversos blocs
  window.criVideoWeb = true;
  document.addEventListener("click", function (event) {
    var button = event.target.closest("[data-video-carrega]");
    if (!button) return;
    var figure = button.closest("[data-video-youtube]");
    var url = figure.getAttribute("data-embed");
    if (url.indexOf("https://www.youtube-nocookie.com/embed/") !== 0) return;
    var frame = document.createElement("iframe");
    frame.className = "zm-vista";
    frame.src = url;
    frame.title = figure.getAttribute("data-titol");
    frame.allow = "autoplay; encrypted-media; picture-in-picture";
    frame.allowFullscreen = true;
    frame.referrerPolicy = "strict-origin-when-cross-origin";
    button.replaceWith(frame);
  });
})();
