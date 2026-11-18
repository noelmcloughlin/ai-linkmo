// The site's own script. Everything it does is an addition: with no script
// the pages, the navigation and its headings still work.

// The reader's choices in the Display menu, kept in this browser. They are
// applied before the page is drawn, so a dark page never flashes light.
const root = document.documentElement;
const defaults = { theme: "auto", size: "medium" };
const prefs = { ...defaults };
try {
  Object.assign(prefs, JSON.parse(localStorage.getItem("ktl-display") || "{}"));
} catch {}

function applyPrefs() {
  root.dataset.theme = prefs.theme;
  root.dataset.size = prefs.size;
  // A figure with a dark version, and the code colours, follow the choice too.
  const media = { auto: "(prefers-color-scheme: dark)", dark: "all", light: "not all" }[prefs.theme];
  for (const el of document.querySelectorAll('source[media*="prefers-color-scheme"], source[data-dark], #code-dark')) {
    el.dataset.dark = "";
    el.media = media;
  }
  // The graph page draws on a canvas, which takes its colours again on this.
  document.dispatchEvent(new Event("displaychange"));
}
applyPrefs();

addEventListener("DOMContentLoaded", () => {
  const menu = document.getElementById("prefs");
  document.getElementById("prefs-open").hidden = false;
  // A choice this browser kept from an older menu, such as a size no longer offered, falls back to the default.
  for (const name of ["theme", "size"]) {
    const offered = [...menu.querySelectorAll(`input[name="${name}"]`)].map((input) => input.value);
    if (!offered.includes(prefs[name])) prefs[name] = defaults[name];
  }
  for (const input of menu.querySelectorAll("input")) {
    input.checked = prefs[input.name] === input.value;
    input.addEventListener("change", () => {
      prefs[input.name] = input.value;
      try {
        localStorage.setItem("ktl-display", JSON.stringify(prefs));
      } catch {}
      applyPrefs();
    });
    // A choice made by pointer closes the menu. One made with the arrow keys leaves it open, since each key press chooses, and Escape closes it.
    input.addEventListener("click", (event) => event.detail && menu.hidePopover());
  }
  // Again now the page is read, for its figures and for a choice that fell back.
  applyPrefs();

  // The navigation is built once per group, so the current page's link is marked here.
  // A page that retells another has no link of its own, and the page it retells is marked.
  const links = [...document.querySelectorAll("#nav a")].filter((a) => !a.hash);
  const here = [location.pathname, new URL(document.getElementById("main").dataset.retells ?? "", location).pathname];
  for (const a of links.filter((a) => a.pathname === here.find((path) => links.some((link) => link.pathname === path)))) {
    a.setAttribute("aria-current", "page");
    a.scrollIntoView({ block: "nearest" });
  }

  // A Copy button on each code block.
  for (const pre of document.querySelectorAll(".prose pre:not(.mermaid)")) {
    const button = Object.assign(document.createElement("button"), { type: "button", className: "copy", textContent: "Copy" });
    button.addEventListener("click", async () => {
      await navigator.clipboard.writeText((pre.querySelector("code") ?? pre).innerText);
      button.textContent = "Copied";
      setTimeout(() => (button.textContent = "Copy"), 1500);
    });
    pre.append(button);
  }

  // A figure or a diagram opens over the page as large as the window allows, by mouse or keyboard. Escape or
  // Close puts it away, so the reader never leaves the page, and so does a click on a figure. A figure's link
  // still names the file, for a new tab.
  let zoom, view, shown;
  const enlarge = (content, label, tools = null) => {
    if (!zoom) {
      zoom = Object.assign(document.createElement("dialog"), { className: "zoom" });
      zoom.innerHTML = '<p class="zoom__tools"><button type="button" data-do="out" aria-label="Zoom out">−</button>'
        + '<button type="button" data-do="in" aria-label="Zoom in">+</button><button type="button" data-do="fit">Fit</button>'
        + '<button type="button" data-do="close">Close</button></p>';
      zoom.addEventListener("click", (event) => {
        const what = event.target.closest("[data-do]")?.dataset.do;
        if (what === "close") zoom.close();
        else if (what) view?.[what]();
        else if (!view || (event.target === zoom && !view.dragged())) zoom.close();
      });
      zoom.addEventListener("keydown", (event) => {
        const what = { "+": "in", "=": "in", "-": "out", 0: "fit" }[event.key];
        if (what && view) (event.preventDefault(), view[what]());
      });
      zoom.addEventListener("close", () => {
        if (view) view.put();
        else shown.remove();
        view = shown = null;
      });
      document.body.append(zoom);
    }
    view = tools;
    shown = content;
    zoom.ariaLabel = label;
    zoom.classList.toggle("zoom--diagram", !!tools);
    zoom.append(content);
    zoom.showModal();
  };

  for (const img of document.querySelectorAll(".prose picture > img, .prose p > img")) {
    if (img.closest("a") || img.width < 200) continue;
    const link = Object.assign(document.createElement("a"), { href: img.currentSrc || img.src, className: "figure", title: "Show the figure at full size" });
    (img.closest("picture") ?? img).replaceWith(link);
    link.append(img.closest("picture") ?? img);
    link.addEventListener("click", (event) => {
      if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      const src = img.currentSrc || img.src;
      // A drawing grows to fill the window. A photograph stops at its own size, where it is still sharp.
      const drawing = /\.svg([?#]|$)/i.test(src);
      const big = Object.assign(document.createElement("img"), { src, alt: img.alt, className: drawing ? "zoom__drawing" : "" });
      big.style.maxWidth = drawing ? "" : `min(100%, ${img.naturalWidth}px)`;
      enlarge(big, "The figure at full size");
    });
  }

  // A Mermaid diagram moves into the same window, where the wheel or the buttons zoom it and a drag moves it.
  // Mermaid draws it after the page loads, so the drawing is looked for on each click, not now.
  for (const pre of document.querySelectorAll(".prose .mermaid")) {
    Object.assign(pre, { tabIndex: 0, title: "Show the diagram at full size" });
    pre.setAttribute("role", "button");
    pre.classList.add("figure");
    const open = () => {
      const svg = pre.querySelector("svg");
      if (svg?.viewBox.baseVal?.width) enlarge(svg, "The diagram at full size", diagramView(svg, pre));
    };
    pre.addEventListener("click", open);
    pre.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") (event.preventDefault(), open());
    });
  }

  // The zoom and the drag change the drawing's viewBox, so it stays sharp at any size. put() returns it to the page as it was.
  function diagramView(svg, home) {
    const style = svg.getAttribute("style");
    const first = svg.getAttribute("viewBox");
    const whole = svg.viewBox.baseVal;
    let box = { x: whole.x, y: whole.y, w: whole.width, h: whole.height };
    const fitted = { ...box };
    let drag = null, moved = 0;
    const draw = () => svg.setAttribute("viewBox", `${box.x} ${box.y} ${box.w} ${box.h}`);
    // Zoom by a factor about a point in the window, the middle of the drawing when none is given.
    const scale = (by, x, y) => {
      const w = Math.min(Math.max(box.w / by, fitted.w / 40), fitted.w * 2);
      const r = svg.getBoundingClientRect();
      const p = new DOMPoint(x ?? r.left + r.width / 2, y ?? r.top + r.height / 2).matrixTransform(svg.getScreenCTM().inverse());
      const k = w / box.w;
      box = { x: p.x - (p.x - box.x) * k, y: p.y - (p.y - box.y) * k, w, h: box.h * k };
      draw();
    };
    const wheel = (event) => (event.preventDefault(), scale(Math.exp(-event.deltaY * 0.002), event.clientX, event.clientY));
    const down = (event) => {
      event.preventDefault();
      drag = { x: event.clientX, y: event.clientY };
      moved = 0;
      svg.setPointerCapture(event.pointerId);
    };
    const move = (event) => {
      if (!drag) return;
      const k = svg.getScreenCTM().a;
      box.x -= (event.clientX - drag.x) / k;
      box.y -= (event.clientY - drag.y) / k;
      moved += Math.abs(event.clientX - drag.x) + Math.abs(event.clientY - drag.y);
      drag = { x: event.clientX, y: event.clientY };
      draw();
    };
    const up = () => (drag = null);
    svg.removeAttribute("style");
    svg.classList.add("zoom__diagram");
    svg.addEventListener("wheel", wheel, { passive: false });
    svg.addEventListener("pointerdown", down);
    svg.addEventListener("pointermove", move);
    svg.addEventListener("pointerup", up);
    svg.addEventListener("pointercancel", up);
    return {
      in: () => scale(1.3),
      out: () => scale(1 / 1.3),
      fit: () => ((box = { ...fitted }), draw()),
      dragged: () => moved > 4,
      put: () => {
        svg.removeEventListener("wheel", wheel);
        svg.removeEventListener("pointerdown", down);
        svg.removeEventListener("pointermove", move);
        svg.removeEventListener("pointerup", up);
        svg.removeEventListener("pointercancel", up);
        svg.classList.remove("zoom__diagram");
        if (style) svg.setAttribute("style", style);
        svg.setAttribute("viewBox", first);
        home.append(svg);
      },
    };
  }

  // Search, once a build has written its index. The preview server has none.
  // Each library is looked for by its type, since an element whose id is
  // its name would otherwise stand in for it.
  const search = document.getElementById("search");
  if (typeof window.PagefindUI === "function") {
    new PagefindUI({ element: search, bundlePath: search.dataset.bundle, showSubResults: true, showImages: false, resetStyles: false });
    search.querySelector("input")?.setAttribute("aria-label", "Search this site");
    // A click on the dimmed page closes the results, as Escape in the box does.
    document.addEventListener("click", (event) => {
      if (!search.contains(event.target) && search.querySelector(".pagefind-ui__drawer:not(.pagefind-ui__hidden)")) search.querySelector(".pagefind-ui__search-clear")?.click();
    });
  }

  // Mermaid keeps the colours it started with, so each diagram's source is kept, and every diagram is drawn
  // again when the Display menu or the system changes the scheme.
  if (typeof window.mermaid?.initialize === "function" && typeof window.mermaid.run === "function") {
    const diagrams = [...document.querySelectorAll(".prose .mermaid")].map((pre) => ({ pre, source: pre.textContent }));
    const colours = () => {
      const probe = document.body.appendChild(document.createElement("span"));
      const color = (name) => {
        probe.style.color = `var(${name})`;
        return getComputedStyle(probe).color;
      };
      const themeVariables = {
        darkMode: matchMedia("(prefers-color-scheme: dark)").matches ? prefs.theme !== "light" : prefs.theme === "dark",
        fontFamily: getComputedStyle(document.body).fontFamily,
        background: color("--bg"),
        primaryColor: color("--card"),
        primaryTextColor: color("--fg"),
        primaryBorderColor: color("--rule"),
        secondaryColor: color("--panel"),
        tertiaryColor: color("--panel"),
        lineColor: color("--muted"),
        textColor: color("--fg"),
      };
      probe.remove();
      return themeVariables;
    };
    let drawn = "";
    const draw = async () => {
      const themeVariables = colours();
      // The Display menu's Text size changes no colour, so the diagrams stay as they are.
      if (JSON.stringify(themeVariables) === drawn) return;
      drawn = JSON.stringify(themeVariables);
      // A diagram open at full size goes back to its place first, and is drawn again there.
      if (zoom?.open && view) {
        view.put();
        view = null;
        zoom.close();
      }
      mermaid.initialize({ startOnLoad: false, theme: "base", themeVariables });
      for (const { pre, source } of diagrams) {
        pre.removeAttribute("data-processed");
        pre.textContent = source;
      }
      await mermaid.run({ nodes: diagrams.map(({ pre }) => pre), suppressErrors: true });
    };
    // One drawing at a time, in the order asked for. The first waits for the page's fonts, which set each label's width.
    let last = Promise.resolve();
    const redraw = () => (last = last.then(draw, draw));
    if (document.readyState === "complete") redraw();
    else addEventListener("load", redraw);
    document.addEventListener("displaychange", redraw);
    matchMedia("(prefers-color-scheme: dark)").addEventListener("change", redraw);
  }
});
