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
  /* Count-up for numbers that are already on the page                   */
  /* ------------------------------------------------------------------ */

  // Animates the leading number of a text node from 0 to its value. Screen
  // readers get the final text throughout, and the original text node is put
  // back unchanged at the end.
  function countUp(node, delay, duration) {
    if (!node || node.nodeType !== 3 || node.__counting) return;
    var text = node.nodeValue;
    var m = /^(\s*)(\d[\d,]*(?:\.\d+)?)/.exec(text);
    if (!m) return;
    var lead = m[1], raw = m[2], rest = text.slice(m[0].length);
    var target = parseFloat(raw.replace(/,/g, ""));
    var dec = (raw.split(".")[1] || "").length;
    var comma = raw.indexOf(",") >= 0;
    function fmt(v) {
      return comma
        ? v.toLocaleString("en-US", { minimumFractionDigits: dec, maximumFractionDigits: dec })
        : v.toFixed(dec);
    }
    var parent = node.parentNode;
    var wrap = document.createElement("span");
    var sr = document.createElement("span");
    var vis = document.createElement("span");
    // The real text keeps its place in the layout (transparent, still read by
    // screen readers) so nothing reflows while the overlaid digits change.
    wrap.className = "count";
    sr.className = "count-real";
    sr.textContent = text;
    vis.className = "count-anim";
    if (getComputedStyle(parent).textAlign === "right") vis.style.justifySelf = "end";
    vis.setAttribute("aria-hidden", "true");
    vis.textContent = lead + fmt(0) + rest;
    vis.style.opacity = "0";
    wrap.appendChild(sr);
    wrap.appendChild(vis);
    parent.replaceChild(wrap, node);
    node.__counting = true;
    var t0 = null;
    function frame(now) {
      if (t0 === null) t0 = now + delay;
      // Nothing is shown until the count starts, so no placeholder value is ever on screen.
      vis.style.opacity = now < t0 ? "0" : "";
      var k = Math.min(1, Math.max(0, (now - t0) / duration));
      var e = 1 - Math.pow(1 - k, 4);
      vis.textContent = lead + fmt(target * e) + rest;
      if (k < 1) requestAnimationFrame(frame);
      else { parent.replaceChild(node, wrap); node.__counting = false; }
    }
    requestAnimationFrame(frame);
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

  window.__omMotion = true;
})();
