/*
 * Efectos de interfaz inspirados en React Bits, en JS vanilla (sin dependencias, compatible con la CSP
 * script-src 'self'). Solo se modifican estilos vía CSSOM (el.style), que la CSP sí permite.
 * Todo es mejora progresiva: si este archivo no carga, las páginas siguen funcionando igual.
 */
(function () {
  "use strict";
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var $$ = function (sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); };

  // Enlace activo en la navegación
  $$(".db-links a").forEach(function (a) {
    if (a.pathname === location.pathname) a.classList.add("active");
  });

  // SplitText / BlurText: anima cada palabra del título
  $$("[data-split]").forEach(function (el) {
    var text = el.textContent.trim();
    el.setAttribute("aria-label", text);
    el.textContent = "";
    el.classList.add("db-split");
    text.split(/(\s+)/).forEach(function (part, i) {
      var s = document.createElement("span");
      s.className = "db-w";
      s.setAttribute("aria-hidden", "true");
      s.textContent = part;
      s.style.animationDelay = (i * 0.045) + "s";
      el.appendChild(s);
    });
  });

  // Aparición escalonada de bloques
  $$(".db-reveal").forEach(function (el, i) { el.style.animationDelay = (0.08 + i * 0.07) + "s"; });

  // AnimatedList: filas de tablas entran en cascada
  $$("table tbody").forEach(function (tb) {
    $$("tr", tb).forEach(function (tr, i) {
      tr.classList.add("db-anim-row");
      tr.style.animationDelay = Math.min(i * 0.04, 0.8) + "s";
    });
  });

  // SpotlightCard: el brillo sigue al cursor
  $$(".db-spot").forEach(function (card) {
    card.addEventListener("pointermove", function (e) {
      var r = card.getBoundingClientRect();
      card.style.setProperty("--mx", (e.clientX - r.left) + "px");
      card.style.setProperty("--my", (e.clientY - r.top) + "px");
    });
  });

  // CountUp
  $$("[data-count]").forEach(function (el) {
    var end = parseInt(el.textContent, 10);
    if (isNaN(end) || reduce) return;
    var start = performance.now(), dur = 1400;
    el.textContent = "0";
    (function tick(now) {
      var t = Math.min((now - start) / dur, 1);
      el.textContent = Math.round(end * (1 - Math.pow(1 - t, 4)));
      if (t < 1) requestAnimationFrame(tick);
    })(start);
  });

  // Barras de ocupación
  $$("[data-meter]").forEach(function (bar) {
    var v = parseFloat(bar.getAttribute("data-meter")) || 0;
    requestAnimationFrame(function () { setTimeout(function () { bar.style.width = Math.max(0, Math.min(100, v)) + "%"; }, 150); });
  });

  // ClickSpark: chispas al hacer clic en botones
  if (!reduce) {
    document.addEventListener("click", function (e) {
      var btn = e.target.closest(".btn, .db-action");
      if (!btn) return;
      var size = 90, c = document.createElement("canvas");
      c.width = c.height = size * 2; c.className = "db-spark";
      c.style.left = (e.clientX - size) + "px"; c.style.top = (e.clientY - size) + "px";
      c.style.width = c.style.height = (size * 2) + "px";
      document.body.appendChild(c);
      var ctx = c.getContext("2d"), t0 = performance.now(), n = 8, colors = ["#a78bfa", "#22d3ee", "#f472b6"];
      (function draw(now) {
        var p = Math.min((now - t0) / 450, 1), ease = 1 - Math.pow(1 - p, 3);
        ctx.clearRect(0, 0, c.width, c.height);
        ctx.lineWidth = 3; ctx.lineCap = "round";
        for (var i = 0; i < n; i++) {
          var a = (Math.PI * 2 * i) / n, d = 20 + ease * 70, len = 22 * (1 - ease);
          ctx.strokeStyle = colors[i % colors.length];
          ctx.beginPath();
          ctx.moveTo(size + Math.cos(a) * d, size + Math.sin(a) * d);
          ctx.lineTo(size + Math.cos(a) * (d + len), size + Math.sin(a) * (d + len));
          ctx.stroke();
        }
        if (p < 1) requestAnimationFrame(draw); else c.remove();
      })(t0);
    });
  }

  // Contador en vivo de pasajeros vs. capacidad (asignación simple y de grupo)
  $$("[data-asignacion]").forEach(function (form) {
    var area = form.querySelector("textarea[name=pasajeros]");
    var box = form.querySelector(".db-counter");
    if (!area || !box) return;
    var outP = box.querySelector("[data-n-pasajeros]"), outC = box.querySelector("[data-n-capacidad]"), state = box.querySelector(".db-state");
    function capacidad() {
      var sel = form.querySelector("select[name=habitacion_id]");
      if (sel) { var o = sel.options[sel.selectedIndex]; return o ? parseInt(o.getAttribute("data-cap"), 10) || 0 : 0; }
      return $$("input[name=habitacion_ids]:checked", form).reduce(function (s, cb) { return s + (parseInt(cb.getAttribute("data-cap"), 10) || 0); }, 0);
    }
    function update() {
      var n = area.value.split(/\r?\n/).filter(function (l) { return l.trim(); }).length, cap = capacidad();
      outP.textContent = n; outC.textContent = cap;
      var ok = n > 0 && n === cap;
      box.classList.toggle("ok", ok); box.classList.toggle("bad", !ok && n > 0);
      state.textContent = ok ? "✓ Cuadra con la capacidad" : (n > 0 ? (n < cap ? "Faltan " + (cap - n) + " pasajero(s)" : "Sobran " + (n - cap) + " pasajero(s)") : "");
    }
    form.addEventListener("input", update);
    form.addEventListener("change", update);
    update();
  });
})();
