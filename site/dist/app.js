"use strict";
let dataset = { exhibition: [], official: [], catalog: [] };
const requestedTrack = new URLSearchParams(location.search).get("track");
let active = ["exhibition", "official"].includes(requestedTrack) ? requestedTrack : "exhibition";
const $ = (id) => document.getElementById(id);
const mediaUrl = (path) => `${path}?v=integrations-4`;
const labels = {
  idle: "Idle / control",
  random: "Random / control",
  react: "Pixel React",
  tracker: "Pixel Tracker",
  astra: "GPT-6 Astra",
  claude: "Claude",
  "mlx-community/SmolVLM2-256M-Video-Instruct-mlx": "SmolVLM2 256M",
  "mlx-community/SmolVLM2-500M-Video-Instruct-mlx": "SmolVLM2 500M",
  "LiquidAI/LFM2.5-VL-450M-MLX-4bit": "LFM2.5-VL 450M · 4 bit",
  "mlx-community/FastVLM-0.5B-bf16": "FastVLM 0.5B · BF16",
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
  const requested = $("score-game").value;
  const available = (dataset[active] || [])[0]?.games || [];
  const game = available.includes(requested) ? requested : "all";
  const all = el("option", "Entire fixed suite");
  all.value = "all";
  $("score-game").replaceChildren(all);
  available.forEach(id => {
    const option = el("option", id);
    option.value = id;
    $("score-game").append(option);
  });
  $("score-game").value = game;
  $("score-game").disabled = !available.length;
  const rows = [...(dataset[active] || [])].sort((a, b) =>
    (game === "all" ? b.score - a.score : b.per_game[game] - a.per_game[game]) || a.agent.localeCompare(b.agent));
  $("rankings").replaceChildren();
  const descriptions = {
    exhibition:
      "Hosted models, local vision models and reference policies use the same 43 scenarios. Each game uses one seed and eight decisions. This short test checks integration. It cannot establish model skill. The suite p95 limit is below 200 ms. Scores stay visible if a model fails this limit. Hosted calls ran concurrently and include CLI startup. Local MLX models run one at a time, after three gray startup images. All game calls count. Run settings show the timing conditions. Failed episodes remain in the results. Incomplete suites receive no aggregate score.",
    official:
      "There are no certified entries. Official admission requires suite p95 below 200 ms, independent isolated execution, hidden evaluation seeds and signed evidence. A local latency pass does not grant an official rank.",
  };
  $("track-description").textContent = descriptions[active];
  if (!rows.length) {
    const tr = el("tr");
    const td = el(
      "td",
      active === "official"
        ? "Official competition is not open yet. Select Model exhibition to see the current results."
        : "No completed measurements in this track.",
      "empty",
    );
    td.colSpan = 8;
    tr.append(td);
    $("rankings").append(tr);
  }
  let rank = 0;
  const scoreOf = r => game === "all" ? r.score : r.per_game[game];
  rows.forEach((r, i) => {
    if (i === 0 || scoreOf(r) < scoreOf(rows[i - 1]) - 1e-9) rank = i + 1;
    const tr = el("tr");
    const name = labels[r.model] || r.model || labels[r.agent] || r.agent;
    const vals = [
      String(rank).padStart(2, "0"),
      name,
      (game === "all" ? r.score : r.per_game[game]).toFixed(1),
      r.ci95 && game === "all"
        ? `${r.ci95[0].toFixed(1)} – ${r.ci95[1].toFixed(1)}`
        : game !== "all" ? "Suite interval only" : "Insufficient seeds",
      ms(r.p95_ms),
      ms(r.max_ms),
      String(r.errors || 0),
    ];
    vals.forEach((v, j) => {
      const cell = el("td", v, j === 0 ? "rank" : "");
      if (j === 4) cell.title = `Unrounded suite p95: ${r.p95_ms} ms`;
      if (j === 1) {
        const transport = r.provider_metadata?.transport;
        cell.append(el("small", transport === "persistent-mlx-jsonl" ? "Local vision model" : transport === "authenticated-cli-per-frame" ? "Hosted model · per-image call" : "Reference policy", "agent-kind"));
        const settings = r.hardware_details || dataset.track_metadata?.[active]?.hardware_details || dataset.hardware_details;
        if (settings) {
          const details = el("details", undefined, "run-settings");
          details.append(el("summary", "Run settings"), el("p", settings));
          cell.append(details);
        }
        if (transport === "persistent-mlx-jsonl" && /^[\w.-]+\/[\w.-]+$/.test(r.model)) {
          const source = el("a", "Model source", "agent-kind");
          source.href = `https://huggingface.co/${r.model}`;
          cell.append(source);
        }
      }
      tr.append(cell);
    });
    const td = el("td");
    td.append(
      el(
        "span",
        r.latency_eligible ? "PASS" : "FAIL",
        r.latency_eligible ? "pass" : "fail",
      ),
    );
    tr.append(td);
    $("rankings").append(tr);
  });
  $("suite").textContent = rows.length
    ? `${game === "all" ? rows[0].games.length + " equally weighted scenarios" : "Scores for " + game} | ${rows[0].seeds} seed(s) per game | ${rows[0].max_steps} decision horizon | ${rows[0].hardware} | lockstep simulation. Timing, errors and the p95 limit below 200 ms always describe the entire suite. Exactly 200 ms fails. ${rows[0].seeds < 2 ? "One seed: no confidence interval. Some games barely start within this horizon." : "Intervals reflect seed variation only."}`
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
      card.id = `environment-${g.id}`;
      const figure = el("figure", undefined, "game-media");
      const image = el("img");
      image.src = mediaUrl(g.image);
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
            image.src = mediaUrl(g.animation);
            play.setAttribute("aria-pressed", "true");
            play.textContent = "Stop preview";
          }
        });
        image.dataset.poster = mediaUrl(g.image);
        figure.append(play);
      } else {
        const preview = el("a", g.preview_label || "View project media", "preview-link");
        preview.href = g.preview_url || g.media_source;
        preview.target = "_blank";
        preview.rel = "noopener noreferrer";
        preview.setAttribute("aria-label", `${preview.textContent} for ${g.name} (opens a new tab)`);
        figure.append(preview);
      }
      const caption = el("figcaption");
      caption.append(el("span", g.media_kind));
      const credit = el("a", g.media_kind === "Recorded benchmark" ? "Recorded evidence" : "Image source");
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
      const tasks = g.task_ids || [];
      card.append(el("p", tasks.length
        ? `${tasks.length} validated ${tasks.length === 1 ? "task" : "tasks"}${g.preview_task ? ` · Preview: ${g.preview_task}` : ""}`
        : "No ranked task yet", "task-coverage"));
      const details = el("details", undefined, "game-details");
      details.append(
        el("summary", "Preview & integration details"),
        el("p", g.media_caption),
        el("p", g.note),
        el("p", g.media_credit, "media-credit"),
      );
      if (tasks.length) {
        const taskList = el("ul", undefined, "task-list");
        tasks.forEach(task => taskList.append(el("li", task)));
        details.append(el("p", "Validated tasks"), taskList);
      }
      if (g.video) {
        const download = el("a", "Download MP4 clip");
        download.href = mediaUrl(g.video);
        download.download = "";
        details.append(download);
      }
      card.append(details);
      const bottom = el("div", undefined, "card-bottom");
      bottom.append(
        el(
          "span",
          ({ validated: "RUNNABLE NOW", "validation-failed": "REPLAY VALIDATION PENDING",
            "runtime-blocked": "RUNTIME BLOCKED", experimental: "EXPERIMENTAL",
            "assets-required": "GAME INSTALL NEEDED", planned: "PLANNED" })[g.integration_state] || "RESEARCH CANDIDATE",
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
    const url = new URL(location.href);
    url.searchParams.set("track", active);
    history.replaceState(null, "", url);
    renderBoard();
  }),
);
$("game-filter").addEventListener("change", renderGames);
$("score-game").addEventListener("change", renderBoard);
fetch("data.json?v=suite-p95-200-v1", { cache: "no-cache" })
  .then((r) => {
    if (!r.ok) throw new Error("Results unavailable");
    return r.json();
  })
  .then((d) => {
    dataset = d;
    const rows = [...(d.exhibition || []), ...(d.official || [])];
    const games = [...new Set(rows.flatMap(r => r.games))];
    $("scenario-count").textContent = d.integration_coverage?.task_count || d.coverage?.task_count || games.length;
    $("availability").replaceChildren();
    (d.model_status || []).forEach(model => {
      $("availability").append(el("li", `${model.model}: ${model.status === "complete" ? `${model.completed} episodes recorded` : model.status}. ${model.error_type ? "Setup failure: " + model.error_type : ""}`));
    });
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
