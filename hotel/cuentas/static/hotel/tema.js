/*
 * Tema claro/oscuro. Se carga en <head> sin "defer" para aplicar el tema antes de pintar la página
 * (evita el parpadeo). La preferencia se guarda en este navegador; sin preferencia guardada se usa la del sistema.
 */
(function () {
  "use strict";
  var raiz = document.documentElement, CLAVE = "db-tema";

  function guardado() {
    try { return localStorage.getItem(CLAVE); } catch (e) { return null; }
  }
  function aplicar(tema) {
    raiz.setAttribute("data-theme", tema);
    raiz.setAttribute("data-bs-theme", tema);
  }
  var inicial = guardado();
  if (inicial !== "light" && inicial !== "dark") {
    inicial = window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
  }
  aplicar(inicial);

  document.addEventListener("DOMContentLoaded", function () {
    var btn = document.querySelector("[data-tema-toggle]");
    if (!btn) return;
    function etiquetar() {
      var claro = raiz.getAttribute("data-theme") === "light";
      btn.setAttribute("aria-label", claro ? "Cambiar a tema oscuro" : "Cambiar a tema claro");
      btn.setAttribute("title", claro ? "Tema oscuro" : "Tema claro");
    }
    etiquetar();
    btn.addEventListener("click", function () {
      var nuevo = raiz.getAttribute("data-theme") === "light" ? "dark" : "light";
      aplicar(nuevo);
      try { localStorage.setItem(CLAVE, nuevo); } catch (e) { /* sin almacenamiento: dura hasta recargar */ }
      etiquetar();
    });
  });
})();
