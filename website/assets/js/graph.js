// The knowledge graph page. It draws graph.json, which `lokf export` writes,
// with Cytoscape: every concept as a node and every typed relation as an
// edge. `?concept=<id>` opens the page on that concept. On a domain host,
// `?graph=workspace` draws the workspace's graph instead, every member
// bundle in a room of its own, and `&iri=<iri>` names a concept there, since
// two bundles may each hold a concept of one id.

// The layout. The concept with the most relations goes in the middle, and the
// rest go on rings round it in order of how many relations each has. Round a
// ring, each concept sits in the direction of the concepts it is related to,
// so related concepts end up side by side. No force is simulated, so the same
// graph draws the same way each time, and a graph of thousands of concepts
// draws at once. Returns the radius of the outermost ring.
function rings(nodes, room = 110, gap = 120) {
  const byDegree = nodes.sort((a, b) => b.data("degree") - a.data("degree") || (a.id() < b.id() ? -1 : 1)).toArray();
  const ring = [[]];
  for (const node of byDegree) {
    const k = ring.length - 1;
    // A ring holds as many concepts as fit round it, each with room for its title.
    if (ring[k].length >= Math.max(1, Math.floor((2 * Math.PI * k * gap) / room))) ring.push([]);
    ring.at(-1).push(node);
  }
  const angle = new Map();
  const place = (members) => {
    // Each concept wants the mean direction of the neighbours placed so far.
    const want = members.map((node, i) => {
      let x = 0;
      let y = 0;
      node.neighborhood("node").forEach((other) => {
        if (!angle.has(other.id())) return;
        x += Math.cos(angle.get(other.id()));
        y += Math.sin(angle.get(other.id()));
      });
      return { node, at: Math.abs(x) + Math.abs(y) > 1e-9 ? Math.atan2(y, x) : (2 * Math.PI * i) / members.length - Math.PI };
    });
    want.sort((a, b) => a.at - b.at);
    // They are spread evenly in that order, and the ring is turned to suit them all best.
    const step = (2 * Math.PI) / want.length;
    let x = 0;
    let y = 0;
    want.forEach((w, i) => {
      x += Math.cos(w.at - i * step);
      y += Math.sin(w.at - i * step);
    });
    const turn = Math.atan2(y, x);
    want.forEach((w, i) => angle.set(w.node.id(), turn + i * step));
  };
  // Once from the middle outward, then again with every neighbour placed.
  for (let pass = 0; pass < 5; pass++) ring.forEach((members, k) => (pass === 0 || k > 0) && place(members));
  ring.forEach((members, k) => members.forEach((node) => node.position({ x: k * gap * Math.cos(angle.get(node.id())), y: k * gap * Math.sin(angle.get(node.id())) })));
  return (ring.length - 1) * gap;
}

addEventListener("DOMContentLoaded", async () => {
  const el = document.getElementById("graph");
  const find = (selector) => el.querySelector(selector);
  const make = (tag, props = {}, ...children) => {
    const node = Object.assign(document.createElement(tag), props);
    node.append(...children);
    return node;
  };
  const extra = JSON.parse(el.dataset.extra);
  // The ladder's states, top first, and the words for each.
  const toneWords = JSON.parse(el.dataset.tones);
  const tones = toneWords.order;
  const query = new URLSearchParams(location.search);
  const workspace = Boolean(el.dataset.workspace) && query.get("graph") === "workspace";
  for (const a of el.querySelectorAll("[data-view]")) if ((a.dataset.view === "workspace") === workspace) a.setAttribute("aria-current", "page");
  // The workspace has a heading and an introduction of its own.
  if (workspace) {
    const heading = document.querySelector("main h1");
    document.title = document.title.replace(heading.textContent, heading.dataset.workspace);
    heading.textContent = heading.dataset.workspace;
    for (const words of document.querySelectorAll("[data-for]")) words.hidden = words.dataset.for !== "workspace";
  }

  const note = find(".graph__note");
  const say = (words) => {
    note.hidden = false;
    note.textContent = words;
  };
  let graph;
  try {
    const answer = await fetch(workspace ? el.dataset.workspace : el.dataset.src);
    // The federation workflow adds the workspace after the site is built, and leaves out one that holds internal metadata.
    if (workspace && answer.status === 404) return say("This site serves no workspace yet. The federation workflow adds it when the domain releases, unless it holds internal metadata, which stays on the release.");
    if (!answer.ok) throw new Error(`${answer.status} ${answer.statusText}`);
    graph = await answer.json();
  } catch (error) {
    return say(`The graph could not be loaded: ${error.message}`);
  }

  // A concept of this bundle has the trust label the report script printed.
  // A workspace's concept has only the tier `lokf export` gave it, shown in
  // lokf's words, and its tone is the nearest of the site's.
  const bundles = new Map((workspace ? graph.meta?.bundles ?? [] : []).map((b) => [b.slug, b]));
  const degree = new Map();
  for (const { data } of graph.edges) for (const end of [data.source, data.target]) degree.set(end, (degree.get(end) ?? 0) + 1);
  for (const { data } of graph.nodes) {
    const own = workspace ? null : extra[data.concept_id];
    data.tone = own?.tone ?? { "human-reviewed": "person", "machine-confirmed": "automation" }[data.trust_tier] ?? "nobody";
    data.trust = own?.trust ?? [data.trust_tier, data.status].filter(Boolean).join(", ");
    data.url = own?.url ?? (workspace && /^https?:\/\//i.test(data.id) ? data.id : "");
    data.degree = degree.get(data.id) ?? 0;
    // A concept with more relations is drawn larger, and so is its title, which then still reads when the whole graph is in view.
    data.size = 9 + Math.sqrt(data.degree) * 4.5;
    data.font = 10 + Math.sqrt(data.degree) * 1.6;
    data.wide = Math.round(data.font * 11);
    if (bundles.has(data.bundle)) data.parent = `room:${data.bundle}`;
  }
  const roomNodes = [...bundles].map(([slug, b]) => ({ data: { id: `room:${slug}`, label: b.version ? `${b.title}, ${b.version}` : b.title, room: true } }));

  // Cytoscape draws on a canvas, which cannot read a CSS variable, so each colour is resolved here.
  const style = () => {
    const probe = document.body.appendChild(document.createElement("span"));
    const color = (name) => {
      probe.style.color = `var(${name})`;
      return "#" + getComputedStyle(probe).color.match(/\d+/g).slice(0, 3).map((n) => Number(n).toString(16).padStart(2, "0")).join("");
    };
    const [fg, stage, line, accent, muted] = ["--fg", "--stage", "--rule", "--accent", "--muted"].map(color);
    const chart = Object.fromEntries(tones.map((tone) => [tone, color(`--chart-${tone}`)]));
    const font = getComputedStyle(document.body).fontFamily;
    probe.remove();
    return [
      // A node is drawn as the site draws a trust dot: filled for a person's confirmation, half filled for an edit since, a ring for automation, a dotted ring for nobody.
      { selector: "node[!room]", style: { label: "data(label)", width: "data(size)", height: "data(size)", "font-size": "data(font)", "font-family": font, color: fg, "text-wrap": "ellipsis", "text-max-width": "data(wide)", "text-margin-y": -3, "min-zoomed-font-size": 6.5, "text-outline-width": 2, "text-outline-color": stage, "background-color": stage, "border-width": 2, "border-color": chart.nobody, "border-style": "dotted", "z-index": "data(degree)" } },
      { selector: 'node[tone = "person"]', style: { "background-color": chart.person, "border-color": chart.person, "border-style": "solid" } },
      { selector: 'node[tone = "edited"]', style: { "border-color": chart.edited, "border-style": "solid", "background-fill": "linear-gradient", "background-gradient-direction": "to-right", "background-gradient-stop-colors": `${chart.edited} ${chart.edited} ${stage} ${stage}`, "background-gradient-stop-positions": "0 50 50 100" } },
      { selector: 'node[tone = "automation"]', style: { "border-color": chart.automation, "border-style": "solid" } },
      { selector: 'node[tone = "retired"]', style: { opacity: 0.6 } },
      // A member bundle's room in a workspace.
      { selector: "node[?room]", style: { label: "data(label)", "font-family": font, shape: "round-rectangle", "background-color": fg, "background-opacity": 0.04, "border-width": 2, "border-style": "dashed", "border-color": line, padding: 50, "font-size": 44, "font-weight": "bold", color: muted, "text-max-width": 900, "text-valign": "top", "text-margin-y": -10 } },
      { selector: "edge", style: { width: 1, "line-color": line, "target-arrow-color": line, "target-arrow-shape": "triangle", "arrow-scale": 0.7, "curve-style": "straight", opacity: 0.4 } },
      { selector: "edge[?cross]", style: { "line-style": "dashed", "line-color": accent, "target-arrow-color": accent, width: 1.5, opacity: 0.8 } },
      { selector: ".dim", style: { opacity: 0.1 } },
      { selector: ".off", style: { display: "none" } },
      { selector: "node.focus", style: { "border-width": 4, "border-style": "solid", "border-color": accent, "font-weight": "bold", "text-max-width": 320, "z-index": 9 } },
      { selector: "edge.focus", style: { width: 1.6, opacity: 1, "line-color": accent, "target-arrow-color": accent, label: "data(slot)", "font-size": 8, "font-family": font, color: fg, "text-rotation": "autorotate", "text-outline-width": 2, "text-outline-color": stage, "min-zoomed-font-size": 6 } },
    ];
  };
  const cy = cytoscape({ container: document.getElementById("cy"), elements: [...roomNodes, ...graph.nodes, ...graph.edges], layout: { name: "preset" }, style: style(), minZoom: 0.02, maxZoom: 3, hideEdgesOnViewport: graph.nodes.length > 600 });
  const concepts = cy.nodes("[!room]");
  document.addEventListener("displaychange", () => cy.style(style()));
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => cy.style(style()));

  // One bundle is one set of rings. A workspace is a set for each bundle: the largest in the middle and the others round it.
  const sets = workspace ? [...new Set(concepts.map((n) => n.data("parent") ?? ""))].map((room) => concepts.filter((n) => (n.data("parent") ?? "") === room)) : [concepts];
  // A room is drawn as a box round its rings, so it is given the circle that box fits in.
  const laid = sets.map((nodes) => ({ nodes, radius: (rings(nodes) + 90) * Math.SQRT2 })).sort((a, b) => b.radius - a.radius);
  const others = laid.slice(1);
  const total = others.reduce((sum, set) => sum + set.radius, 0);
  const around = Math.max(laid[0].radius + Math.max(0, ...others.map((set) => set.radius)), total / Math.PI);
  let turn = -Math.PI / 2;
  for (const set of others) {
    turn += (Math.PI * set.radius) / total;
    const [x, y] = [around * Math.cos(turn), around * Math.sin(turn)];
    set.nodes.positions((node) => ({ x: node.position("x") + x, y: node.position("y") + y }));
    turn += (Math.PI * set.radius) / total;
  }
  // What the filters leave showing. A relation shows when it and both its ends do. Cytoscape's own `:visible` is not asked, since it lags a class that was just changed.
  const showing = (ele) => !ele.hasClass("off") && (ele.isNode() || (!ele.source().hasClass("off") && !ele.target().hasClass("off")));
  const fit = () => cy.fit(cy.elements().filter(showing), 30);
  fit();

  // The filters: a list of boxes for each way to narrow the graph, with All and None.
  const off = {};
  const status = find(".graph__status");
  const apply = () => {
    concepts.forEach((node) => node.toggleClass("off", ["tone", "type", "bundle"].some((key) => off[key]?.has(node.data(key)))));
    cy.edges().forEach((edge) => edge.toggleClass("off", off.slot.has(edge.data("slot"))));
    // A room with no concept showing is not drawn.
    cy.nodes("[?room]").forEach((room) => room.toggleClass("off", !room.children().some(showing)));
    const [shown, drawn] = [concepts, cy.edges()].map((eles) => eles.filter(showing).length);
    status.textContent = shown === concepts.length && drawn === cy.edges().length ? `${shown} concepts, ${drawn} relations` : `${shown} of ${concepts.length} concepts and ${drawn} of ${cy.edges().length} relations shown`;
  };
  const filter = (title, key, values, words = (value) => value, mark = () => "", order = null) => {
    const count = new Map();
    for (const value of values) count.set(value, (count.get(value) ?? 0) + 1);
    off[key] = new Set();
    if (!count.size) return;
    const boxes = [];
    const set = (box, on) => {
      box.checked = on;
      off[key][on ? "delete" : "add"](box.value);
    };
    const all = (on) => make("button", { type: "button", textContent: on ? "All" : "None", onclick: () => (boxes.forEach((box) => set(box, on)), apply()) });
    const list = make("ul");
    for (const value of [...count.keys()].sort((a, b) => (order ? order.indexOf(a) - order.indexOf(b) : words(a).localeCompare(words(b))))) {
      const box = make("input", { type: "checkbox", checked: true, value, onchange: () => (set(box, box.checked), apply()) });
      boxes.push(box);
      list.append(make("li", {}, make("label", {}, box, mark(value), make("span", { textContent: words(value) }), make("span", { className: "count", textContent: count.get(value) }))));
    }
    // On a narrow screen the lists start closed, so the graph is on the first screen.
    find(".graph__filters").append(make("details", { className: "filter", open: innerWidth > 800 }, make("summary", {}, title, make("span", { className: "count", textContent: count.size })), make("p", { className: "filter__all" }, all(true), all(false)), list));
  };
  filter("Bundles", "bundle", concepts.filter((n) => bundles.has(n.data("bundle"))).map((n) => n.data("bundle")), (slug) => bundles.get(slug).title);
  // A workspace's concepts carry lokf's tier and no label of the report script, so the list names the tiers in lokf's words.
  const tiers = { person: "Human-reviewed", automation: "Machine-confirmed", nobody: "Unverified" };
  filter(workspace ? "Trust tier" : "Trust", "tone", concepts.map((n) => n.data("tone")), (tone) => (workspace ? tiers : toneWords)[tone], (tone) => make("span", { className: `dot dot--${tone}` }), tones);
  filter("Types", "type", concepts.map((n) => n.data("type")));
  filter("Relations", "slot", cy.edges().map((e) => e.data("slot")), (slot) => slot.replace(/([a-z])([A-Z])/g, "$1 $2").replace(/^./, (c) => c.toUpperCase()).replace(/ ./g, (c) => c.toLowerCase()));
  apply();

  // The record of the concept the reader chose: what it is, how far it is trusted, and each relation as a step to the concept at its other end.
  const detail = document.getElementById("graph-detail");
  const key = workspace ? "iri" : "concept";
  const address = (id) => {
    const url = new URL(location.href);
    url.search = new URLSearchParams([...(workspace ? [["graph", "workspace"]] : []), ...(id ? [[key, id]] : [])]).toString().replace(/%2F/g, "/").replace(/%3A/g, ":");
    history.replaceState(history.state, "", url);
  };
  // The concepts given, in the part of the graph the record does not cover.
  const frame = (eles) => {
    cy.fit(eles, 60);
    const covered = detail.hidden || detail.offsetWidth > cy.width() / 2 ? 0 : detail.offsetWidth + 12;
    cy.zoom({ level: Math.min(cy.zoom(), 1.6) * (1 - covered / cy.width()), renderedPosition: { x: 0, y: cy.height() / 2 } });
  };
  const show = (node, focus = true) => {
    concepts.removeClass("focus").addClass("dim");
    cy.edges().removeClass("focus").addClass("dim");
    node.closedNeighborhood().removeClass("dim").edges().addClass("focus");
    node.addClass("focus");
    const data = node.data();
    detail.hidden = false;
    detail.querySelector("h2").textContent = data.label;
    detail.querySelector(".muted").textContent = [data.type, bundles.get(data.bundle)?.title].filter(Boolean).join(" in ");
    Object.assign(detail.querySelector(".label"), { className: `label label--${data.tone}`, textContent: data.trust || "no trust recorded" });
    const link = detail.querySelector("a");
    link.parentElement.hidden = !data.url;
    link.href = data.url || "#";
    link.textContent = workspace ? "Follow its IRI" : "Open the concept page";
    const lists = [];
    for (const [words, edges, end] of [["Points at", node.outgoers("edge").filter(showing), "target"], ["Pointed to by", node.incomers("edge").filter(showing), "source"]]) {
      if (edges.empty()) continue;
      const items = edges.sort((a, b) => a[end]().data("label").localeCompare(b[end]().data("label"))).map((edge) => {
        const other = edge[end]();
        return make("li", {}, make("button", { type: "button", onclick: () => (show(other), cy.animate({ center: { eles: other } }, { duration: 200 })) }, make("span", { className: `dot dot--${other.data("tone")}` }), make("span", {}, other.data("label"), make("span", { className: "muted", textContent: ` (${edge.data("slot")})` }))));
      });
      lists.push(make("h3", { textContent: `${words}: ${edges.length}` }), make("ul", {}, ...items));
    }
    detail.querySelector("div").replaceChildren(...lists);
    // The focus goes to the record, so a reader at the keyboard is among its relations and Escape closes it.
    if (focus) detail.focus({ preventScroll: true });
    address(workspace ? data.id : data.concept_id);
  };
  const close = () => {
    detail.hidden = true;
    cy.elements().removeClass("dim focus");
    address("");
    // What the search box holds dims the graph again.
    search.dispatchEvent(new Event("input"));
  };
  cy.on("tap", "node[!room]", (event) => show(event.target));
  cy.on("tap", (event) => event.target === cy && !detail.hidden && close());
  find(".graph__close").addEventListener("click", close);
  detail.addEventListener("keydown", (event) => event.key === "Escape" && close());

  // Search dims what does not match, and Enter opens the first match.
  const search = document.getElementById("graph-search");
  const matches = () => concepts.filter((node) => showing(node) && node.data("label").toLowerCase().includes(search.value.trim().toLowerCase()));
  search.addEventListener("input", () => {
    const found = search.value.trim() ? matches() : concepts;
    concepts.removeClass("focus").forEach((node) => node.toggleClass("dim", !found.contains(node)));
    cy.edges().removeClass("focus").toggleClass("dim", found.length < concepts.length);
  });
  search.addEventListener("keydown", (event) => {
    const first = event.key === "Enter" && search.value.trim() && matches().sort((a, b) => a.data("label").length - b.data("label").length)[0];
    if (first) (show(first), frame(first.closedNeighborhood()));
  });

  // The tools. Full screen puts the whole explorer on the screen, or over the page where the browser has no full screen for an element.
  const full = find('[data-do="full"]');
  const filled = () => document.fullscreenElement === el || el.classList.contains("graph--fill");
  const resized = () => {
    full.textContent = filled() ? "Leave full screen" : "Full screen";
    full.setAttribute("aria-pressed", filled());
    requestAnimationFrame(() => (cy.resize(), fit()));
  };
  const zoom = (by) => cy.zoom({ level: cy.zoom() * by, renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 } });
  const tools = {
    in: () => zoom(1.3),
    out: () => zoom(1 / 1.3),
    fit,
    full: () => {
      if (document.fullscreenElement) document.exitFullscreen();
      else if (el.requestFullscreen) el.requestFullscreen();
      else (el.classList.toggle("graph--fill"), resized());
    },
  };
  for (const button of el.querySelectorAll("[data-do]")) button.addEventListener("click", tools[button.dataset.do]);
  document.addEventListener("fullscreenchange", resized);

  const wanted = query.get(key);
  const node = wanted && concepts.filter((n) => n.data(workspace ? "id" : "concept_id") === wanted);
  if (node?.length) {
    show(node[0], false);
    frame(node.closedNeighborhood());
  }
});
