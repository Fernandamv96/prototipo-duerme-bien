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

  // Fechas escritas a mano (dd-mm-aaaa) con botón de calendario
  function fechaIso(texto) {
    var m = (texto || "").match(/^(\d{1,2})[-\/](\d{1,2})[-\/](\d{4})$/);
    if (!m) return "";
    var d = new Date(+m[3], +m[2] - 1, +m[1]);
    if (d.getFullYear() !== +m[3] || d.getMonth() !== +m[2] - 1 || d.getDate() !== +m[1]) return "";
    return m[3] + "-" + ("0" + m[2]).slice(-2) + "-" + ("0" + m[1]).slice(-2);
  }
  $$(".db-fecha").forEach(function (caja) {
    var txt = caja.querySelector("[data-fecha]"), btn = caja.querySelector("[data-fecha-btn]"), pick = caja.querySelector("[data-fecha-picker]");
    txt.addEventListener("input", function (e) {
      if (e.inputType && e.inputType.indexOf("delete") === 0) return;   // al borrar no se reinsertan guiones
      var dig = txt.value.replace(/\D/g, "").slice(0, 8), v = dig.slice(0, 2);
      if (dig.length > 2) v += "-" + dig.slice(2, 4);
      if (dig.length > 4) v += "-" + dig.slice(4);
      if (dig.length === 2 || dig.length === 4) v += "-";
      txt.value = v;
    });
    btn.addEventListener("click", function () {
      pick.value = fechaIso(txt.value);
      if (pick.showPicker) { try { pick.showPicker(); return; } catch (e) { /* navegador sin showPicker */ } }
      pick.focus(); pick.click();
    });
    pick.addEventListener("change", function () {
      var p = pick.value.split("-");
      if (p.length === 3) txt.value = p[2] + "-" + p[1] + "-" + p[0];
      txt.dispatchEvent(new Event("input", { bubbles: true }));
    });
  });

  // Número de habitación: solo dígitos
  $$("[data-solo-numeros]").forEach(function (el) {
    el.addEventListener("input", function () { el.value = el.value.replace(/\D/g, ""); });
  });

  function telefonoValido(t) { return /^\+?\d{8,15}$/.test((t || "").replace(/[\s\-()]/g, "")); }
  // misma regla que hotel/reglas.py (correo_valido)
  function correoValido(c) {
    return !c || (c.length <= 254 && c.indexOf("..") < 0 &&
      /^[A-Za-z0-9._%+-]+@[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)*\.[A-Za-z]{2,}$/.test(c));
  }

  // Asignación simple y de grupo: filas de pasajeros, validación en vivo, responsable/representante, capacidad y total
  $$("[data-asignacion]").forEach(function (form) {
    var cont = form.querySelector("[data-filas]");
    var box = form.querySelector(".db-counter");
    if (!cont || !box) return;
    var modelo = cont.querySelector("[data-fila]").cloneNode(true);
    var outP = box.querySelector("[data-n-pasajeros]"), outC = box.querySelector("[data-n-capacidad]"), state = box.querySelector(".db-state");
    var outN = box.querySelector("[data-n-noches]"), outT = box.querySelector("[data-total]");
    var ini = form.querySelector("input[name=fecha_inicio]"), ter = form.querySelector("input[name=fecha_termino]");
    var selHab = form.querySelector("select[name=habitacion_id]"), foto = form.querySelector("[data-foto]");
    var inCant = form.querySelector("[data-cantidad]"), selRep = form.querySelector("[data-representante]");

    // Tantas filas como "Cantidad de pasajeros" (se conservan los datos ya escritos)
    function ajustarFilas() {
      var cant = Math.max(1, Math.min(parseInt(inCant.value, 10) || 1, parseInt(inCant.max, 10) || 60));
      var filas = $$("[data-fila]", cont);
      for (var i = filas.length; i < cant; i++) {
        var f = modelo.cloneNode(true);
        $$("input", f).forEach(function (inp) { inp.value = ""; inp.classList.remove("is-invalid"); });
        cont.appendChild(f);
      }
      filas = $$("[data-fila]", cont);
      for (var j = filas.length - 1; j >= cant; j--) filas[j].remove();
      $$("[data-fila]", cont).forEach(function (f, k) {
        f.querySelector(".db-pax-n").textContent = k + 1;
        $$("input", f).forEach(function (inp) {
          inp.setAttribute("aria-label", inp.getAttribute("aria-label").replace(/pasajero \d+/, "pasajero " + (k + 1)));
        });
      });
    }

    function pasajeros() {
      var vistos = {};
      return $$("[data-fila]", cont).map(function (f, k) {
        var get = function (n) { return f.querySelector("[name=pasajero_" + n + "]"); };
        var nom = get("nombre"), rut = get("rut"), tel = get("telefono"), cor = get("correo");
        var p = { fila: f, nombre: nom.value.trim(), vacia: !(nom.value.trim() || rut.value.trim() || tel.value.trim() || cor.value.trim()), error: "" };
        var rutN = normalizarRut(rut.value);
        var malos = [];
        if (!p.nombre) malos.push([nom, "falta el nombre"]);
        if (!rut.value.trim()) malos.push([rut, "falta el RUT"]);
        else if (!rutN) malos.push([rut, "RUT inválido: " + motivoRutInvalido(rut.value)]);
        else if (vistos[rutN]) malos.push([rut, "RUT repetido"]);
        else vistos[rutN] = true;
        if (!tel.value.trim()) malos.push([tel, "falta el teléfono"]);
        else if (!telefonoValido(tel.value)) malos.push([tel, "teléfono inválido (solo números, p. ej. +56 9 1234 5678)"]);
        if (!correoValido(cor.value.trim())) malos.push([cor, "correo inválido"]);
        [nom, rut, tel, cor].forEach(function (inp) {
          var malo = malos.some(function (m) { return m[0] === inp; });
          // solo se marca en rojo lo que ya se tocó, para no llenar de errores una fila recién creada
          inp.classList.toggle("is-invalid", malo && (inp.value.trim() !== "" || inp.dataset.tocado === "1"));
          inp.setCustomValidity(malo ? malos.filter(function (m) { return m[0] === inp; })[0][1] : "");
        });
        var visibles = malos.filter(function (m) { return m[0].value.trim() !== "" || m[0].dataset.tocado === "1"; });
        f.querySelector(".db-pax-msg").textContent = visibles.map(function (m) { return m[1]; }).join(" · ");
        p.error = malos.length ? malos[0][1] : "";
        p.nombre = p.nombre || "Pasajero " + (k + 1);
        return p;
      });
    }
    function noches() {
      var a = ini && Date.parse(fechaIso(ini.value)), b = ter && Date.parse(fechaIso(ter.value));
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
      var pax = pasajeros(), habs = habitaciones(), noc = noches();
      var completos = pax.filter(function (p) { return !p.vacia; }), n = pax.length;
      var cap = habs.reduce(function (s, h) { return s + h.cap; }, 0);
      var malos = pax.filter(function (p) { return p.error && !p.vacia; }), vacias = pax.filter(function (p) { return p.vacia; });

      [ini, ter].forEach(function (f) { if (f) f.setCustomValidity(fechaIso(f.value) ? "" : "Escriba la fecha como dd-mm-aaaa."); });
      if (ter && ini && fechaIso(ter.value) && fechaIso(ini.value) && noc < 1) ter.setCustomValidity("La fecha de término debe ser posterior a la de inicio.");

      // Responsable y representante: listas con los nombres de los pasajeros
      var nombres = pax.map(function (p) { return p.nombre; }), porHab = {};
      if (selRep) opciones(selRep, nombres, "Ingrese los pasajeros primero");
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
      var habVacias = habs.length > 1 && n > 0 ? habs.filter(function (h) { return !(porHab[h.id] || []).length; }) : [];
      var problema = vacias.length ? "Faltan los datos de " + vacias.length + " pasajero(s)"
        : malos.length ? malos.length + " pasajero(s) con datos por corregir"
        : n > cap ? "Sobran " + (n - cap) + " pasajero(s)"
        : habVacias.length ? "La habitación " + habVacias[0].num + " quedaría vacía"
        : noc < 1 ? "Revise las fechas" : "";
      var ok = completos.length > 0 && !problema;
      box.classList.toggle("ok", ok); box.classList.toggle("bad", !ok && completos.length > 0);
      state.textContent = completos.length === 0 ? "" : ok ? "✓ Listo para confirmar" : problema;
    }
    cont.addEventListener("focusout", function (e) { if (e.target.matches("input")) { e.target.dataset.tocado = "1"; update(); } });
    // Al intentar confirmar con datos inválidos el navegador no envía el formulario: se muestran todos los errores
    form.addEventListener("invalid", function () { $$("input", cont).forEach(function (i) { i.dataset.tocado = "1"; }); update(); }, true);
    form.addEventListener("input", function (e) { if (e.target === inCant) ajustarFilas(); update(); });
    form.addEventListener("change", function (e) {
      if (e.target === selHab && foto) foto.src = selHab.options[selHab.selectedIndex].getAttribute("data-foto");
      update();
    });
    ajustarFilas();
    update();
  });
})();
