// OdorMap landing: animation layer.
//
// Presentation only. Every number, label and drawing it animates is already in
// the HTML; this script only changes how it arrives on screen, and always leaves
// the original text and the original RDKit SVG geometry in place when it is done.
//
// Runs only when the head script has set html.motion (no reduced-motion
// preference, IntersectionObserver available). Without it the page is static
// and complete. Uses transform / opacity / SVG stroke only.
(function () {
  "use strict";
  var root = document.documentElement;
  if (!root.classList.contains("motion")) return;

  var EASE = "cubic-bezier(0.16, 1, 0.3, 1)";
  var finePointer = window.matchMedia("(hover: hover) and (pointer: fine)").matches;

  /* ------------------------------------------------------------------ */
  /* Structure SVGs: fetch once, inline, draw bond by bond               */
  /* ------------------------------------------------------------------ */

  var svgCache = {};
  function loadSvg(url) {
    if (!svgCache[url]) {
      svgCache[url] = fetch(url)
        .then(function (r) { if (!r.ok) throw new Error(url); return r.text(); })
        .then(function (text) {
          var doc = new DOMParser().parseFromString(text, "image/svg+xml");
          var el = doc.documentElement;
          if (!el || el.nodeName.toLowerCase() !== "svg" || doc.querySelector("parsererror")) throw new Error(url);
          return el;
        });
      svgCache[url].catch(function () {});
    }
    return svgCache[url];
  }

  // Swap an <img> of an RDKit drawing for an inline copy of the same SVG file,
  // so its bond paths can be animated. Resolves with the inline <svg>.
  function inlineStructure(img) {
    if (img.__mol) return Promise.resolve(img.__mol);
    return loadSvg(img.getAttribute("src")).then(function (src) {
      if (img.__mol) return img.__mol;
      var svg = document.importNode(src, true);
      svg.setAttribute("class", (img.getAttribute("class") || "") + " mol");
      svg.setAttribute("role", "img");
      svg.setAttribute("aria-label", img.getAttribute("alt") || "");
      svg.setAttribute("focusable", "false");
      img.__mol = svg;
      return svg;
    });
  }

  function ends(path) {
    var n = (path.getAttribute("d") || "").match(/-?\d+(?:\.\d+)?/g) || [];
    return [[+n[0], +n[1]], [+n[n.length - 2], +n[n.length - 1]]];
  }

  // Draw the molecule the way a chemist would: start at the first atom of the
  // SMILES and walk outward through the bond graph. Bond paths are drawn with
  // stroke-dashoffset; heteroatom labels fade in when their bond arrives.
  function drawStructure(svg, opt) {
    if (svg.__anims) svg.__anims.forEach(function (a) { a.cancel(); });
    var anims = [];
    svg.__anims = anims;

    var bonds = {}, labels = {}, extra = [], adj = {};
    Array.prototype.forEach.call(svg.querySelectorAll("path"), function (p) {
      var c = (p.getAttribute("class") || "").trim();
      var m = /\bbond-(\d+) atom-(\d+) atom-(\d+)/.exec(c);
      if (m) {
        var b = bonds[m[1]] || (bonds[m[1]] = { a: +m[2], b: +m[3], paths: [] });
        b.paths.push(p);
      } else if ((m = /^atom-(\d+)$/.exec(c))) {
        (labels[m[1]] = labels[m[1]] || []).push(p);
      } else {
        extra.push(p);
      }
    });
    var atomIds = {};
    Object.keys(bonds).forEach(function (k) {
      var b = bonds[k];
      (adj[b.a] = adj[b.a] || []).push(b);
      (adj[b.b] = adj[b.b] || []).push(b);
      atomIds[b.a] = atomIds[b.b] = true;
    });
    Object.keys(labels).forEach(function (k) { atomIds[k] = true; });
    var atoms = Object.keys(atomIds).map(Number).sort(function (x, y) { return x - y; });

    // Breadth-first walk from the lowest atom index (the first atom in the SMILES).
    var reached = {}, done = {}, total = 0;
    var step = opt.bond * 0.82;
    atoms.forEach(function (start) {
      if (start in reached) return;
      reached[start] = opt.delay;
      var queue = [start];
      while (queue.length) {
        var at = queue.shift();
        (adj[at] || []).forEach(function (b) {
          if (b.done) return;
          b.done = true;
          var other = b.a === at ? b.b : b.a;
          b.t = reached[at];
          b.forward = b.a === at;
          if (!(other in reached)) { reached[other] = b.t + step; queue.push(other); }
          total = Math.max(total, b.t + opt.bond);
        });
      }
    });

    Object.keys(bonds).forEach(function (k) {
      var b = bonds[k];
      var p0 = ends(b.paths[0])[0], far = p0, best = -1;
      b.paths.forEach(function (p) {
        ends(p).forEach(function (q) {
          var d = (q[0] - p0[0]) * (q[0] - p0[0]) + (q[1] - p0[1]) * (q[1] - p0[1]);
          if (d > best) { best = d; far = q; }
        });
      });
      var ax = far[0] - p0[0], ay = far[1] - p0[1], len2 = ax * ax + ay * ay || 1;
      function t(q) { return Math.min(1, Math.max(0, ((q[0] - p0[0]) * ax + (q[1] - p0[1]) * ay) / len2)); }
      b.paths.forEach(function (p) {
        var e = ends(p), ts = t(e[0]), te = t(e[1]);
        var lo = Math.min(ts, te), hi = Math.max(ts, te);
        var w0 = b.forward ? lo : 1 - hi, w1 = b.forward ? hi : 1 - lo;
        var fromStart = (te >= ts) === b.forward;
        p.setAttribute("pathLength", "1");
        anims.push(p.animate(
          [{ strokeDasharray: "1 1", strokeDashoffset: fromStart ? 1 : -1 },
           { strokeDasharray: "1 1", strokeDashoffset: 0 }],
          { duration: Math.max(16, (w1 - w0) * opt.bond), delay: b.t + w0 * opt.bond, fill: "both", easing: "linear" }
        ));
      });
    });

    Object.keys(labels).forEach(function (k) {
      var at = k in reached ? reached[k] : opt.delay;
      labels[k].forEach(function (p) {
        p.style.transformBox = "fill-box";
        p.style.transformOrigin = "center";
        anims.push(p.animate(
          [{ opacity: 0, transform: "scale(0.55)" }, { opacity: 1, transform: "none" }],
          { duration: 320, delay: Math.max(0, at - 40), fill: "both", easing: EASE }
        ));
      });
      total = Math.max(total, at + 320);
    });

    // Small join pieces at ring corners: settle in as the skeleton completes.
    extra.forEach(function (p) {
      anims.push(p.animate([{ opacity: 0 }, { opacity: 1 }],
        { duration: 220, delay: Math.max(opt.delay, total - 260), fill: "both" }));
    });

    // Afterwards, drop every animation so the SVG is exactly the RDKit original.
    Promise.all(anims.map(function (a) { return a.finished; })).then(function () {
      if (svg.__anims !== anims) return;
      anims.forEach(function (a) { a.cancel(); });
      Array.prototype.forEach.call(svg.querySelectorAll("path[pathLength]"), function (p) { p.removeAttribute("pathLength"); });
      Object.keys(labels).forEach(function (k) {
        labels[k].forEach(function (p) { p.style.transformBox = ""; p.style.transformOrigin = ""; });
      });
      svg.__anims = null;
    }, function () {});
    return total;
  }

  function placeAndDraw(img, opt) {
    return inlineStructure(img).then(function (svg) {
      if (img.parentNode) img.replaceWith(svg);
      drawStructure(svg, opt);
      return svg;
    });
  }

  /* ------------------------------------------------------------------ */
  /* Arrival for numbers that are already on the page                    */
  /* ------------------------------------------------------------------ */

  // Presentation only: the number's real, final text is on screen from the
  // first frame and is never rewritten. No intermediate values are generated.
  // Only how it arrives is animated: a short rise, a blur-to-sharp settle and a
  // hairline that draws in underneath and fades. The original text node is put
  // back unchanged at the end. (Name kept for the call sites below.)
  function countUp(node, delay, duration) {
    if (!node || node.nodeType !== 3 || node.__counting) return;
    var parent = node.parentNode;
    if (!parent || typeof parent.animate !== "function") return;
    var wrap = document.createElement("span");
    var line = document.createElement("span");
    wrap.className = "count";
    line.className = "count-line";
    line.setAttribute("aria-hidden", "true");
    parent.replaceChild(wrap, node);
    wrap.appendChild(node);          // the same text node, real value, untouched
    wrap.appendChild(line);
    node.__counting = true;
    var settle = wrap.animate([
      { opacity: 0.45, transform: "translateY(0.22em)", filter: "blur(3px)" },
      { opacity: 1, transform: "none", filter: "blur(0)" }
    ], { duration: duration * 0.7, delay: delay, easing: EASE, fill: "backwards" });
    var draw = line.animate([
      { transform: "scaleX(0)", opacity: 1 },
      { transform: "scaleX(1)", opacity: 1, offset: 0.6 },
      { transform: "scaleX(1)", opacity: 0 }
    ], { duration: duration, delay: delay, easing: "ease-out", fill: "both" });
    function done() {
      if (wrap.parentNode === parent) parent.replaceChild(node, wrap);
      node.__counting = false;
    }
    Promise.all([settle.finished, draw.finished]).then(done, done);
  }

  function firstText(el) {
    for (var n = el.firstChild; n; n = n.nextSibling) {
      if (n.nodeType === 3 && /\d/.test(n.nodeValue)) return n;
    }
    return null;
  }

  /* ------------------------------------------------------------------ */
  /* Hero                                                                */
  /* ------------------------------------------------------------------ */

  var HERO_DRAW = { delay: 520, bond: 230 };
  var heroImg = document.querySelector(".specimen-img");
  if (heroImg) {
    var shown = false;
    var fallback = setTimeout(function () { if (!shown) heroImg.classList.add("is-fallback"); }, 2500);
    placeAndDraw(heroImg, HERO_DRAW).then(function (svg) {
      shown = true;
      clearTimeout(fallback);
      var holder = svg.parentNode;
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "redraw";
      btn.innerHTML = '<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M16.5 10a6.5 6.5 0 1 1-1.9-4.6"/><path d="M15 2.5v3.2h-3.2"/></svg>Redraw structure';
      btn.addEventListener("click", function () { drawStructure(svg, { delay: 0, bond: HERO_DRAW.bond }); });
      holder.appendChild(btn);
    }, function () {
      clearTimeout(fallback);
      heroImg.classList.add("is-fallback");
    });
  }

  Array.prototype.forEach.call(document.querySelectorAll(".facts dd"), function (dd, i) {
    countUp(firstText(dd), 650 + i * 90, 1300);
  });
  Array.prototype.forEach.call(document.querySelectorAll(".specimen-scores .s-val"), function (el, i) {
    countUp(firstText(el), 1450 + i * 70, 900);
  });

  /* ------------------------------------------------------------------ */
  /* Hero background: drifting fragments of skeletal formulas            */
  /* ------------------------------------------------------------------ */

  // Generic fragments (a ring, a zigzag chain, a branch point) drawn the way the
  // page draws structures. Decorative only: they stand for no molecule and no data.
  function heroField(hero) {
    var canvas = document.createElement("canvas");
    var ctx = canvas.getContext && canvas.getContext("2d");
    if (!ctx) return;
    canvas.className = "hero-field";
    canvas.setAttribute("aria-hidden", "true");
    hero.insertBefore(canvas, hero.firstChild);

    var S3 = Math.sqrt(3) / 2;
    var TEMPLATES = [
      { // six-membered ring with one substituent
        pts: [[0, -1], [S3, -0.5], [S3, 0.5], [0, 1], [-S3, 0.5], [-S3, -0.5], [0, -2]],
        edges: [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 0], [0, 6]],
        inner: [[1, 2], [3, 4], [5, 0]]
      },
      { // zigzag chain
        pts: [[-2 * S3, 0], [-S3, 0.5], [0, 0], [S3, 0.5], [2 * S3, 0], [3 * S3, 0.5]],
        edges: [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5]],
        inner: []
      },
      { // branch point
        pts: [[0, 0], [0, -1], [-S3, 0.5], [S3, 0.5], [2 * S3, 0], [S3, 1.5]],
        edges: [[0, 1], [0, 2], [0, 3], [3, 4], [3, 5]],
        inner: [[3, 5]]
      }
    ];

    var seed = 7;
    function rand() { // small deterministic PRNG, so the field looks the same on every load
      seed = (seed + 0x6d2b79f5) | 0;
      var t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    }

    // Phones: the fragments move 1-6 px per second, so redrawing at 15 fps and 1x
    // density moves them under half a pixel per step and keeps main-thread work low.
    var lite = !finePointer || window.innerWidth < 700;
    var frameGap = lite ? 1000 / 15 - 2 : 0;
    var w = 0, h = 0, frags = [], running = false, onscreen = true, last = 0, raf = 0;
    var px = 0, py = 0, tx = 0, ty = 0;

    function seedField() {
      frags = [];
      var n = w < 700 ? 7 : 13;
      var cols = Math.ceil(Math.sqrt(n * w / h)), rows = Math.ceil(n / cols);
      for (var i = 0; i < n; i++) {
        var depth = 0.45 + rand() * 0.55;
        frags.push({
          tpl: TEMPLATES[i % TEMPLATES.length],
          x: ((i % cols) + 0.15 + rand() * 0.7) / cols * w,
          y: (Math.floor(i / cols) + 0.15 + rand() * 0.7) / rows * h,
          s: 13 + depth * 15,
          a: rand() * Math.PI * 2,
          va: (rand() - 0.5) * 0.08,
          vx: (rand() - 0.5) * 6 * depth,
          vy: -(1.5 + rand() * 3.5) * depth,
          depth: depth
        });
      }
    }

    function resize() {
      var r = hero.getBoundingClientRect();
      var dpr = lite ? 1 : Math.min(window.devicePixelRatio || 1, 1.5);
      var first = !w;
      // On phones the lower hero is mostly the specimen card: only cover the first screen.
      w = r.width; h = lite ? Math.min(r.height, window.innerHeight) : r.height;
      canvas.style.height = h + "px";
      canvas.width = Math.round(w * dpr);
      canvas.height = Math.round(h * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      if (first) seedField();
      draw();
    }

    function draw() {
      ctx.clearRect(0, 0, w, h);
      ctx.lineCap = "round";
      ctx.lineJoin = "round";
      for (var i = 0; i < frags.length; i++) {
        var f = frags[i], c = Math.cos(f.a) * f.s, sn = Math.sin(f.a) * f.s;
        var ox = f.x + px * f.depth, oy = f.y + py * f.depth;
        var P = f.tpl.pts.map(function (p) { return [ox + p[0] * c - p[1] * sn, oy + p[0] * sn + p[1] * c]; });
        var alpha = 0.05 + 0.1 * f.depth;
        ctx.strokeStyle = "rgba(94,230,214," + alpha.toFixed(3) + ")";
        ctx.fillStyle = ctx.strokeStyle;
        ctx.lineWidth = 1.1 + f.depth * 0.5;
        ctx.beginPath();
        f.tpl.edges.forEach(function (e) { ctx.moveTo(P[e[0]][0], P[e[0]][1]); ctx.lineTo(P[e[1]][0], P[e[1]][1]); });
        // inner line of a double bond, pulled toward the fragment centre
        f.tpl.inner.forEach(function (e) {
          var a = P[e[0]], b = P[e[1]];
          var mx = (a[0] + b[0]) / 2, my = (a[1] + b[1]) / 2, k = 0.2;
          var dx = (ox - mx) * k, dy = (oy - my) * k;
          ctx.moveTo(a[0] + dx + (b[0] - a[0]) * 0.15, a[1] + dy + (b[1] - a[1]) * 0.15);
          ctx.lineTo(b[0] + dx - (b[0] - a[0]) * 0.15, b[1] + dy - (b[1] - a[1]) * 0.15);
        });
        ctx.stroke();
        ctx.beginPath();
        for (var j = 0; j < P.length; j++) { ctx.moveTo(P[j][0] + 1.6, P[j][1]); ctx.arc(P[j][0], P[j][1], 1.6, 0, 6.2832); }
        ctx.fill();
      }
    }

    function tick(now) {
      if (now - last < frameGap) { raf = requestAnimationFrame(tick); return; }
      var dt = Math.min(0.05, (now - last) / 1000 || 0);
      last = now;
      px += (tx - px) * 0.05;
      py += (ty - py) * 0.05;
      for (var i = 0; i < frags.length; i++) {
        var f = frags[i];
        f.x += f.vx * dt; f.y += f.vy * dt; f.a += f.va * dt;
        if (f.y < -70) { f.y = h + 70; f.x = rand() * w; }
        if (f.x < -70) f.x = w + 70; else if (f.x > w + 70) f.x = -70;
      }
      draw();
      raf = requestAnimationFrame(tick);
    }

    function sync() {
      var go = onscreen && !document.hidden;
      if (go && !running) { running = true; last = performance.now(); raf = requestAnimationFrame(tick); }
      else if (!go && running) { running = false; cancelAnimationFrame(raf); }
      hero.classList.toggle("is-offscreen", !onscreen);
    }

    new IntersectionObserver(function (entries) {
      onscreen = entries[entries.length - 1].isIntersecting;
      sync();
    }).observe(hero);
    document.addEventListener("visibilitychange", sync);
    if ("ResizeObserver" in window) new ResizeObserver(resize).observe(hero);
    else window.addEventListener("resize", resize);
    resize();

    if (finePointer) {
      hero.addEventListener("pointermove", function (e) {
        tx = (e.clientX / window.innerWidth - 0.5) * -18;
        ty = (e.clientY / window.innerHeight - 0.5) * -18;
      }, { passive: true });
      hero.addEventListener("pointerleave", function () { tx = ty = 0; });
    }
  }

  var hero = document.querySelector(".hero");
  if (hero) heroField(hero);

  /* ------------------------------------------------------------------ */
  /* Pointer tilt (desktop)                                              */
  /* ------------------------------------------------------------------ */

  function tilt(el, maxDeg) {
    if (!finePointer || !el) return;
    var raf = 0, rx = 0, ry = 0;
    el.classList.add("tilt");
    el.addEventListener("pointermove", function (e) {
      var r = el.getBoundingClientRect();
      ry = ((e.clientX - r.left) / r.width - 0.5) * 2 * maxDeg;
      rx = -((e.clientY - r.top) / r.height - 0.5) * 2 * maxDeg;
      if (!raf) raf = requestAnimationFrame(function () {
        raf = 0;
        el.classList.add("is-tilting");
        el.style.transform = "perspective(900px) rotateX(" + rx.toFixed(2) + "deg) rotateY(" + ry.toFixed(2) + "deg)";
      });
    }, { passive: true });
    el.addEventListener("pointerleave", function () {
      cancelAnimationFrame(raf);
      raf = 0;
      el.classList.remove("is-tilting");
      el.style.transform = "";
    });
  }

  tilt(document.querySelector(".specimen"), 2.5);

  // Buttons lean a few pixels toward the pointer.
  if (finePointer) {
    Array.prototype.forEach.call(document.querySelectorAll(".btn-primary, .head-repo"), function (el) {
      var raf = 0, dx = 0, dy = 0;
      el.classList.add("magnetic");
      el.addEventListener("pointermove", function (e) {
        var r = el.getBoundingClientRect();
        dx = Math.max(-6, Math.min(6, (e.clientX - r.left - r.width / 2) * 0.18));
        dy = Math.max(-4, Math.min(4, (e.clientY - r.top - r.height / 2) * 0.3));
        if (!raf) raf = requestAnimationFrame(function () {
          raf = 0;
          el.classList.add("is-pulled");
          el.style.transform = "translate(" + dx.toFixed(1) + "px," + dy.toFixed(1) + "px)";
        });
      }, { passive: true });
      el.addEventListener("pointerleave", function () {
        cancelAnimationFrame(raf);
        raf = 0;
        el.classList.remove("is-pulled");
        el.style.transform = "";
      });
    });
  }

  /* ------------------------------------------------------------------ */
  /* Scroll reveals                                                      */
  /* ------------------------------------------------------------------ */

  var hooks = [];
  function onReveal(selector, fn) { hooks.push([selector, fn]); }
  function runHooks(el) {
    hooks.forEach(function (h) { if (el.matches(h[0])) h[1](el); });
  }
  function show(el) {
    if (el.classList.contains("in")) return;
    el.classList.add("in");
    runHooks(el);
  }

  var revealIO = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) { revealIO.unobserve(e.target); show(e.target); }
    });
  }, { rootMargin: "0px 0px -10% 0px" });

  // The page end can never reach the -10% line, so the last blocks use no margin.
  var revealEndIO = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) { revealEndIO.unobserve(e.target); show(e.target); }
    });
  });

  function reveal(selector, stagger, cols, observer) {
    Array.prototype.forEach.call(document.querySelectorAll(selector), function (el, i) {
      // Anything already on screen (or scrolled past) is never hidden.
      if (el.getBoundingClientRect().top < window.innerHeight * 0.92) { show(el); return; }
      if (stagger) el.style.setProperty("--rv-d", ((cols ? i % cols : i) * stagger) + "ms");
      el.setAttribute("data-rv", "");
      (observer || revealIO).observe(el);
    });
  }

  // Never leave keyboard focus inside something that is still transparent.
  document.addEventListener("focusin", function (e) {
    var el = e.target.closest && e.target.closest("[data-rv]:not(.in)");
    while (el) {
      show(el);
      el = el.parentElement && el.parentElement.closest("[data-rv]:not(.in)");
    }
  });

  onReveal(".eval-split", function (el) {
    Array.prototype.forEach.call(el.querySelectorAll(".metrics tbody td"), function (td, i) {
      countUp(firstText(td), 250 + i * 160, 1400);
    });
  });

  /* ------------------------------------------------------------------ */
  /* Examples                                                            */
  /* ------------------------------------------------------------------ */

  var PANEL_DRAW = { delay: 140, bond: 150 };
  var examples = document.querySelector(".examples");

  function animatePanel(panel) {
    var holder = panel.querySelector(".panel-structure");
    if (holder) {
      var img = holder.querySelector("img");
      if (img) placeAndDraw(img, PANEL_DRAW).catch(function () {});
      else if (holder.querySelector(".mol")) drawStructure(holder.querySelector(".mol"), PANEL_DRAW);
    }
    Array.prototype.forEach.call(panel.querySelectorAll(".d-val"), function (el, i) {
      countUp(firstText(el), 180 + i * 45, 900);
    });
  }

  if (examples) {
    // Fetch the nine drawings shortly before the section arrives.
    var prefetchIO = new IntersectionObserver(function (entries) {
      if (!entries[entries.length - 1].isIntersecting) return;
      prefetchIO.disconnect();
      Array.prototype.forEach.call(examples.querySelectorAll(".panel-structure img"), function (img) {
        loadSvg(img.getAttribute("src"));
      });
    }, { rootMargin: "600px 0px" });
    prefetchIO.observe(examples);

    onReveal(".examples", function (el) {
      var open = el.querySelector('[role="tabpanel"]:not([hidden])');
      if (open) animatePanel(open);
    });

    var tablist = examples.querySelector('[role="tablist"]');
    if (tablist) tablist.addEventListener("om:select", function (e) {
      if (e.detail.input === "pointer" && examples.classList.contains("in")) animatePanel(e.detail.panel);
    });

    Array.prototype.forEach.call(examples.querySelectorAll(".panel-structure"), function (el) { tilt(el, 6); });
  }

  // Hooks are registered before reveal() so blocks already on screen run them too.
  reveal(".band h2:not(.data-grid h2)");
  reveal(".band .section-lede");
  reveal(".pipeline > li", 110);
  reveal(".band .examples");
  reveal(".eval-split, .eval-calib", 120);
  reveal(".limits > li", 90, 3);
  reveal(".data-grid > div", 140);
  reveal(".site-foot .foot-row", 0, 0, revealEndIO);

  var chart = document.querySelector(".calib");
  if (chart) {
    var chartIO = new IntersectionObserver(function (entries) {
      if (entries[entries.length - 1].isIntersecting) { chart.classList.add("in"); chartIO.disconnect(); }
    }, { threshold: 0.35 });
    chartIO.observe(chart);
  }

  window.__omMotion = true;
})();
