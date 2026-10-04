"use strict";
let dataset = { local: [], exhibition: [], catalog: [] };
let active = "local";
const $ = (id) => document.getElementById(id);
const labels = {
  idle: "Idle / control",
  random: "Random / control",
  react: "Pixel React",
  tracker: "Pixel Tracker",
  astra: "GPT-6 Astra",
  claude: "Claude",
};
const ms = (n) =>
  n >= 1000 ? `${(n / 1000).toFixed(2)} s` : `${n.toFixed(2)} ms`;
function el(tag, text, cls) {
  const e = document.createElement(tag);
  if (text !== undefined) e.textContent = text;
  if (cls) e.className = cls;
  return e;
}
function renderBoard() {
  const rows = dataset[active] || [];
  $("rankings").replaceChildren();
  const descriptions = {
    local:
      "Measured local baseline runs. Provisional rankings on a fixed suite; sub-100 ms eligibility is reported separately from trust.",
    exhibition:
      "Actual model gameplay with a fresh authenticated CLI call for every image. Startup is included in reaction time. Two seeds and short episodes are a smoke test, not a robust model comparison.",
    official:
      "No certified entries yet. Admission requires independent isolated execution, hidden evaluation seeds and signed runner evidence. Local results cannot promote themselves.",
  };
  $("track-description").textContent = descriptions[active];
  if (!rows.length) {
    const tr = el("tr");
    const td = el(
      "td",
      active === "official"
        ? "Official competition is not open yet. Explore the measured local and exhibition results."
        : "No completed measurements in this track.",
      "empty",
    );
    td.colSpan = 7;
    tr.append(td);
    $("rankings").append(tr);
  }
  rows.forEach((r, i) => {
    const tr = el("tr");
    const name = r.model || labels[r.agent] || r.agent;
    const vals = [
      String(i + 1).padStart(2, "0"),
      name,
      r.score.toFixed(1),
      r.ci95
        ? `${r.ci95[0].toFixed(1)} – ${r.ci95[1].toFixed(1)}`
        : "Insufficient seeds",
      ms(r.p95_ms),
      ms(r.max_ms),
    ];
    vals.forEach((v, j) => tr.append(el("td", v, j === 0 ? "rank" : "")));
    const td = el("td");
    td.append(
      el(
        "span",
        r.latency_eligible
          ? "PASS"
          : r.mode === "exhibition"
            ? "EXHIBITION"
            : "FAIL",
        r.latency_eligible ? "pass" : "fail",
      ),
    );
    tr.append(td);
    $("rankings").append(tr);
  });
  $("suite").textContent = rows.length
    ? `${rows[0].games.join(" · ")} | ${rows[0].seeds} seeds per game | ${rows[0].max_steps} decision horizon | ${rows[0].hardware} | lockstep simulation | intervals reflect seed variation only`
    : "";
  document.querySelectorAll("[data-track]").forEach((b) => {
    b.classList.toggle("active", b.dataset.track === active);
    b.setAttribute("aria-pressed", String(b.dataset.track === active));
  });
}
function renderGames() {
  const filter = $("game-filter").value;
  $("game-grid").replaceChildren();
  dataset.catalog
    .filter((g) => filter === "all" || g.status === filter)
    .forEach((g) => {
      const card = el("article", undefined, "game-card");
      const figure = el("figure", undefined, "game-media");
      const image = el("img");
      image.src = g.image;
      image.alt = g.image_alt;
      image.loading = "lazy";
      image.decoding = "async";
      image.width = 640;
      image.height = 360;
      figure.append(image);
      if (g.animation) {
        const play = el("button", "Play preview", "preview-toggle");
        play.type = "button";
        play.setAttribute("aria-pressed", "false");
        play.setAttribute(
          "aria-label",
          `Play or stop ${g.name} gameplay preview`,
        );
        play.addEventListener("click", () => {
          const wasPlaying = play.getAttribute("aria-pressed") === "true";
          document.querySelectorAll(".preview-toggle").forEach((other) => {
            other.setAttribute("aria-pressed", "false");
            other.textContent = "Play preview";
            const still = other.parentElement.querySelector("img");
            still.src = still.dataset.poster;
          });
          if (!wasPlaying) {
            image.src = g.animation;
            play.setAttribute("aria-pressed", "true");
            play.textContent = "Stop preview";
          }
        });
        image.dataset.poster = g.image;
        figure.append(play);
      }
      const caption = el("figcaption");
      caption.append(el("span", g.media_kind));
      const credit = el("a", "Image source");
      credit.href = g.media_source;
      credit.target = "_blank";
      credit.rel = "noopener noreferrer";
      credit.title = g.media_credit;
      caption.append(credit);
      figure.append(caption);
      card.append(
        figure,
        el("span", g.category, "category"),
        el("h3", g.name),
        el("p", g.description),
      );
      const details = el("details", undefined, "game-details");
      details.append(
        el("summary", "Preview & integration details"),
        el("p", g.media_caption),
        el("p", g.note),
        el("p", g.media_credit, "media-credit"),
      );
      if (g.video) {
        const download = el("a", "Download MP4 clip");
        download.href = g.video;
        download.download = "";
        details.append(download);
      }
      card.append(details);
      const bottom = el("div", undefined, "card-bottom");
      bottom.append(
        el(
          "span",
          g.status === "runnable" ? "RUNNABLE NOW" : "RESEARCH CANDIDATE",
          `status ${g.status}`,
        ),
      );
      const a = el("a", "Project");
      a.href = g.url;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      bottom.append(a);
      card.append(bottom);
      $("game-grid").append(card);
    });
}
document.querySelectorAll("[data-track]").forEach((b) =>
  b.addEventListener("click", () => {
    active = b.dataset.track;
    renderBoard();
  }),
);
$("game-filter").addEventListener("change", renderGames);
fetch("data.json")
  .then((r) => {
    if (!r.ok) throw new Error("Results unavailable");
    return r.json();
  })
  .then((d) => {
    dataset = d;
    const rows = [...d.local, ...d.exhibition];
    $("episodes").textContent = rows
      .reduce((n, r) => n + r.episodes, 0)
      .toLocaleString();
    $("decisions").textContent = rows
      .reduce((n, r) => n + r.decisions, 0)
      .toLocaleString();
    $("catalog-count").textContent = d.catalog.filter(
      (g) => g.status === "candidate",
    ).length;
    renderBoard();
    renderGames();
  })
  .catch(() => {
    $("track-description").textContent =
      "Results could not be loaded. Reload this page or view the published evidence on GitHub.";
  });
