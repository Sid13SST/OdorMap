// OdorMap landing: keyboard-accessible tabs for the recorded examples
// (WAI-ARIA tabs pattern, manual activation by click, automatic on arrow keys).
// Without this script every example is shown stacked (see styles.css).
// Animation lives in motion.js; this file only reports how a tab was chosen
// ("pointer" or "key") so keyboard switching can stay near-instant.
(function () {
  "use strict";
  var list = document.querySelector('[role="tablist"]');
  if (!list) return;
  var tabs = Array.prototype.slice.call(list.querySelectorAll('[role="tab"]'));
  var examples = list.closest(".examples") || list.parentNode;

  // Sliding indicator beside (desktop) or under (narrow screens) the active tab.
  var ink = document.createElement("span");
  ink.className = "tab-ink";
  ink.setAttribute("aria-hidden", "true");
  list.appendChild(ink);

  function placeInk() {
    var tab = list.querySelector('[aria-selected="true"]');
    if (!tab) return;
    var row = getComputedStyle(list).flexDirection === "row";
    var x = tab.offsetLeft, y = tab.offsetTop, w = tab.offsetWidth, h = tab.offsetHeight;
    // The ink is a 100px bar scaled to the tab, so only transform changes.
    ink.style.transform = row
      ? "translate(" + (x + 12) + "px," + (y + h - 2) + "px) scale(" + Math.max(0, w - 24) / 100 + ",1)"
      : "translate(" + x + "px," + (y + 9) + "px) scale(1," + Math.max(0, h - 18) / 100 + ")";
    ink.classList.toggle("is-row", row);
  }

  function select(tab, focus, input) {
    var changed = tab.getAttribute("aria-selected") !== "true";
    examples.setAttribute("data-input", input);
    var shown = null;
    tabs.forEach(function (t) {
      var on = t === tab;
      t.setAttribute("aria-selected", on ? "true" : "false");
      t.tabIndex = on ? 0 : -1;
      var panel = document.getElementById(t.getAttribute("aria-controls"));
      if (panel) { panel.hidden = !on; if (on) shown = panel; }
    });
    if (focus) tab.focus();
    placeInk();
    // Keep the active tab visible when the list scrolls sideways on small screens.
    if (list.scrollWidth > list.clientWidth) {
      var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      tab.scrollIntoView({ block: "nearest", inline: "nearest", behavior: reduce || input === "key" ? "auto" : "smooth" });
    }
    if (changed && shown) {
      list.dispatchEvent(new CustomEvent("om:select", { detail: { panel: shown, input: input } }));
    }
  }

  list.addEventListener("click", function (e) {
    var tab = e.target.closest('[role="tab"]');
    // detail === 0: a click synthesised from Enter/Space on the focused button.
    if (tab) select(tab, false, e.detail === 0 ? "key" : "pointer");
  });

  list.addEventListener("keydown", function (e) {
    var i = tabs.indexOf(document.activeElement);
    if (i < 0) return;
    var next = null;
    switch (e.key) {
      case "ArrowDown":
      case "ArrowRight": next = tabs[(i + 1) % tabs.length]; break;
      case "ArrowUp":
      case "ArrowLeft": next = tabs[(i - 1 + tabs.length) % tabs.length]; break;
      case "Home": next = tabs[0]; break;
      case "End": next = tabs[tabs.length - 1]; break;
      default: return;
    }
    e.preventDefault();
    select(next, true, "key");
  });

  placeInk();
  if ("ResizeObserver" in window) new ResizeObserver(placeInk).observe(list);
  else window.addEventListener("resize", placeInk);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(placeInk);
  // Only animate the ink once it has its first position.
  requestAnimationFrame(function () { ink.classList.add("is-ready"); });
})();

// Header state: mark the nav link of the section in view, and shade the header
// once the page has scrolled. IntersectionObserver only, no scroll handlers.
(function () {
  "use strict";
  if (!("IntersectionObserver" in window)) return;
  var head = document.querySelector(".site-head");
  var hero = document.querySelector(".hero");
  if (head && hero) {
    // A 1px sentinel at the top of the hero: once it slips under the header, the page has scrolled.
    var sentinel = document.createElement("div");
    sentinel.className = "top-sentinel";
    sentinel.setAttribute("aria-hidden", "true");
    hero.insertBefore(sentinel, hero.firstChild);
    new IntersectionObserver(function (entries) {
      head.classList.toggle("is-scrolled", !entries[entries.length - 1].isIntersecting);
    }, { rootMargin: "-" + (head.offsetHeight + 1) + "px 0px 0px 0px" }).observe(sentinel);
  }
  var links = {};
  Array.prototype.forEach.call(document.querySelectorAll('.nav a[href^="#"]'), function (a) {
    links[a.getAttribute("href").slice(1)] = a;
  });
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      var a = links[e.target.id];
      if (a) a.classList.toggle("is-current", e.isIntersecting);
    });
  }, { rootMargin: "-45% 0px -50% 0px" });
  Object.keys(links).forEach(function (id) {
    var section = document.getElementById(id);
    if (section) io.observe(section);
  });
})();
