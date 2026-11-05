// OdorMap landing: keyboard-accessible tabs for the recorded examples
// (WAI-ARIA tabs pattern, manual activation by click, automatic on arrow keys).
// Without this script every example is shown stacked (see styles.css).
(function () {
  "use strict";
  var list = document.querySelector('[role="tablist"]');
  if (!list) return;
  var tabs = Array.prototype.slice.call(list.querySelectorAll('[role="tab"]'));

  function select(tab, focus) {
    tabs.forEach(function (t) {
      var on = t === tab;
      t.setAttribute("aria-selected", on ? "true" : "false");
      t.tabIndex = on ? 0 : -1;
      var panel = document.getElementById(t.getAttribute("aria-controls"));
      if (panel) panel.hidden = !on;
    });
    if (focus) tab.focus();
    // Keep the active tab visible when the list scrolls sideways on small screens.
    if (list.scrollWidth > list.clientWidth) {
      var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      tab.scrollIntoView({ block: "nearest", inline: "nearest", behavior: reduce ? "auto" : "smooth" });
    }
  }

  list.addEventListener("click", function (e) {
    var tab = e.target.closest('[role="tab"]');
    if (tab) select(tab, false);
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
    select(next, true);
  });
})();
