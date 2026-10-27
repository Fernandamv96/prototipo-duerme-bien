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

  // RUT chileno: misma regla que hotel/reglas.py (normalizar_rut). Devuelve "12345678-K" o null.
  function partesRut(rut) {
    return (rut || "").replace(/[.\s]/g, "").toUpperCase().match(/^(\d{7,8})-?([0-9K])$/);
  }
  function digitoVerificador(cuerpo) {
    var suma = 0, factor = 2;
    for (var i = cuerpo.length - 1; i >= 0; i--) {
      suma += parseInt(cuerpo[i], 10) * factor;
      factor = factor === 7 ? 2 : factor + 1;
    }
    var resto = 11 - (suma % 11);
    return resto === 11 ? "0" : resto === 10 ? "K" : String(resto);
  }
  function normalizarRut(rut) {
    var m = partesRut(rut);
    return m && m[2] === digitoVerificador(m[1]) ? parseInt(m[1], 10) + "-" + m[2] : null;
  }
  function motivoRutInvalido(rut) {
    var m = partesRut(rut);
    return m ? "el dígito verificador debería ser " + digitoVerificador(m[1]) : "use el formato 12345678-5";
  }

  function opciones(sel, nombres, vacio) {
    var prev = sel.value;
    sel.textContent = "";
    (nombres.length ? nombres : [vacio]).forEach(function (nombre, i) {
      var o = document.createElement("option");
      o.value = String(i + 1); o.textContent = nombre;
      sel.appendChild(o);
    });
    if (prev && parseInt(prev, 10) <= nombres.length) sel.value = prev;
  }

  // Asignación simple y de grupo: RUT en vivo, responsable por nombre, capacidad y total a cobrar
  $$("[data-asignacion]").forEach(function (form) {
    var area = form.querySelector("textarea[name=pasajeros]");
    var box = form.querySelector(".db-counter");
    if (!area || !box) return;
    var outP = box.querySelector("[data-n-pasajeros]"), outC = box.querySelector("[data-n-capacidad]"), state = box.querySelector(".db-state");
    var outN = box.querySelector("[data-n-noches]"), outT = box.querySelector("[data-total]");
    var lista = form.querySelector("[data-rut-check]");
    var ini = form.querySelector("input[name=fecha_inicio]"), ter = form.querySelector("input[name=fecha_termino]");
    var selHab = form.querySelector("select[name=habitacion_id]");

    function pasajeros() {
      var vistos = {};
      return area.value.split(/\r?\n/).filter(function (l) { return l.trim(); }).map(function (l) {
        var partes = l.split(";"), nombre = (partes[0] || "").trim(), rut = partes.slice(1).join(";").trim();
        var p = { nombre: nombre || "(sin nombre)", rut: rut, error: "" };
        var rutN = normalizarRut(rut);
        if (partes.length < 2 || !nombre || !rut) p.error = "Use el formato Nombre;RUT";
        else if (!rutN) p.error = "RUT inválido: " + motivoRutInvalido(rut);
        else if (vistos[rutN]) p.error = "RUT repetido";
        else vistos[rutN] = true;
        return p;
      });
    }
    function noches() {
      var a = ini && Date.parse(ini.value), b = ter && Date.parse(ter.value);
      return a && b ? Math.round((b - a) / 86400000) : 0;
    }
    // Habitaciones elegidas en el mismo orden que usa el servidor: mayor capacidad primero, luego número
    function habitaciones() {
      if (selHab) {
        var o = selHab.options[selHab.selectedIndex];
        return o ? [{ cap: parseInt(o.getAttribute("data-cap"), 10) || 0, precio: parseInt(o.getAttribute("data-precio"), 10) || 0 }] : [];
      }
      return $$("input[name=habitacion_ids]:checked", form).map(function (cb) {
        return { id: cb.value, num: cb.getAttribute("data-num"), cap: parseInt(cb.getAttribute("data-cap"), 10) || 0,
                 precio: parseInt(cb.getAttribute("data-precio"), 10) || 0 };
      }).sort(function (x, y) { return y.cap - x.cap || (x.num < y.num ? -1 : x.num > y.num ? 1 : 0); });
    }
    function update() {
      var pax = pasajeros(), n = pax.length, habs = habitaciones(), noc = noches();
      var cap = habs.reduce(function (s, h) { return s + h.cap; }, 0);
      var malos = pax.filter(function (p) { return p.error; });

      lista.textContent = "";
      pax.forEach(function (p) {
        var li = document.createElement("li");
        li.className = p.error ? "bad" : "ok";
        li.textContent = (p.error ? "✗ " : "✓ ") + p.nombre + " — " + (p.rut || "sin RUT") + (p.error ? " (" + p.error + ")" : "");
        lista.appendChild(li);
      });
      area.setCustomValidity(malos.length ? "Corrija los RUT marcados en rojo." : "");
      if (ter && ini) { ter.min = ini.value; ter.setCustomValidity(ini.value && noc < 1 ? "La fecha de término debe ser posterior a la de inicio." : ""); }

      // Responsable: lista con los nombres de los pasajeros que quedan en cada habitación
      var nombres = pax.map(function (p) { return p.nombre; }), porHab = {};
      if (selHab) opciones(form.querySelector("[data-responsable]"), nombres, "Ingrese los pasajeros primero");
      else {
        var desde = 0;
        habs.forEach(function (h) { porHab[h.id] = nombres.slice(desde, desde + h.cap); desde += h.cap; });
        $$("[data-responsable-hab]", form).forEach(function (sel) {
          var id = sel.getAttribute("data-responsable-hab");
          opciones(sel, porHab[id] || [], id in porHab ? "Sin pasajeros asignados" : "Seleccione la habitación");
        });
      }

      outP.textContent = n; outC.textContent = cap; outN.textContent = noc > 0 ? noc : 0;
      // Cada habitación cobra su precio por los pasajeros que le tocan (mismo reparto que el servidor)
      var resto = n, total = selHab ? n * ((habs[0] || {}).precio || 0)
        : habs.reduce(function (s, h) { var k = Math.min(resto, h.cap); resto -= k; return s + k * h.precio; }, 0);
      outT.textContent = "$" + (total * Math.max(noc, 0)).toLocaleString("es-CL");
      var vacias = habs.length > 1 && n > 0 ? habs.filter(function (h) { return !(porHab[h.id] || []).length; }) : [];
      var problema = malos.length ? malos.length + " RUT con error"
        : n > cap ? "Sobran " + (n - cap) + " pasajero(s)"
        : vacias.length ? "La habitación " + vacias[0].num + " quedaría vacía"
        : noc < 1 ? "Revise las fechas" : "";
      var ok = n > 0 && !problema;
      box.classList.toggle("ok", ok); box.classList.toggle("bad", !ok && n > 0);
      state.textContent = n === 0 ? "" : ok ? "✓ Listo para confirmar" : problema;
    }
    form.addEventListener("input", update);
    form.addEventListener("change", update);
    update();
  });
})();
