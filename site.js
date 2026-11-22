const platformContent = {
  mac: {
    label: "MACOS 14 OR LATER",
    title: "Your Mac, your mood.",
    description: "A universal build for Apple silicon and Intel. Read Spotify or Apple Music playback, choose a visual style, and make the lyric view yours.",
    details: [
      "10 visualizer styles and deep display controls",
      "Original lyrics, transliteration, and imported translations",
      "Optional Auto Sync with supported on-device speech languages",
      "Optional video backgrounds with the supported player source",
      "On-device assistant when Apple's model is available"
    ],
    footnote: "Mac build: ad-hoc signed and not notarized. macOS may show a first-open security prompt.",
    artClass: "platform-art-mac",
    panelLabel: "tab-mac",
  },
  windows: {
    label: "WINDOWS 11 24H2+ RECOMMENDED",
    title: "Windows, in the flow.",
    description: "Choose x64 for most Intel or AMD laptops, or ARM64 for ARM devices. Aurafy reads the active Windows media session from supported players.",
    details: [
      "Responsive full-screen lyric visualizer and media controls",
      "Reads players that publish a Windows media session",
      "Manual Offset and Pace controls plus LRC or text imports",
      "Live Auto Sync is in development and not in the current download",
      "Optional on-device AI on Windows 11 24H2+"
    ],
    footnote: "Early access builds are unsigned and may show a Windows SmartScreen notice. Windows launch and player-session checks on physical devices are still needed.",
    artClass: "platform-art-windows",
    panelLabel: "tab-windows",
  }
};

const tabs = [...document.querySelectorAll(".platform-tab")];
const panel = document.querySelector("#platform-panel");
const art = document.querySelector("#platform-art");

function selectPlatform(name, moveFocus = false) {
  const data = platformContent[name];
  if (!data) return;
  for (const tab of tabs) {
    const selected = tab.dataset.platform === name;
    tab.classList.toggle("is-selected", selected);
    tab.setAttribute("aria-selected", String(selected));
    tab.tabIndex = selected ? 0 : -1;
    if (selected && moveFocus) tab.focus();
  }
  panel.setAttribute("aria-labelledby", data.panelLabel);
  document.querySelector("#platform-kicker").textContent = data.label;
  document.querySelector("#platform-name").textContent = data.title;
  document.querySelector("#platform-description").textContent = data.description;
  document.querySelector("#platform-footnote").textContent = data.footnote;
  const downloadLabel = document.querySelector("#platform-download").firstChild;
  downloadLabel.textContent = `See ${name === "mac" ? "Mac" : "Windows"} downloads `;
  document.querySelector("#platform-details").replaceChildren(
    ...data.details.map((detail, index) => {
      const item = document.createElement("li");
      const number = document.createElement("span");
      number.textContent = String(index + 1).padStart(2, "0");
      item.append(number, document.createTextNode(` ${detail}`));
      return item;
    })
  );
  art.className = `platform-art ${data.artClass}`;
  const note = art.querySelector(".platform-art-note");
  const noteAccent = document.createElement("em");
  note.replaceChildren(document.createTextNode(name === "mac" ? "a song" : "your music"), document.createElement("br"), noteAccent);
  noteAccent.textContent = name === "mac" ? "in focus" : "in view";
  art.querySelector(".platform-art-bottom span:first-child").textContent = name === "mac" ? "Aurafy / MAC" : "Aurafy / WINDOWS";
  art.querySelector(".platform-art-bottom span:last-child").textContent = name === "mac" ? "14+" : "11 / 10 LTSC";
}

tabs.forEach((tab, index) => {
  tab.addEventListener("click", () => selectPlatform(tab.dataset.platform));
  tab.addEventListener("keydown", event => {
    if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
    event.preventDefault();
    let next = index;
    if (event.key === "ArrowRight") next = (index + 1) % tabs.length;
    if (event.key === "ArrowLeft") next = (index - 1 + tabs.length) % tabs.length;
    if (event.key === "Home") next = 0;
    if (event.key === "End") next = tabs.length - 1;
    selectPlatform(tabs[next].dataset.platform, true);
  });
});

const menuButton = document.querySelector(".menu-toggle");
const navigation = document.querySelector(".site-nav");
menuButton.addEventListener("click", () => {
  const opening = menuButton.getAttribute("aria-expanded") !== "true";
  menuButton.setAttribute("aria-expanded", String(opening));
  menuButton.setAttribute("aria-label", opening ? "Close navigation" : "Open navigation");
  navigation.classList.toggle("is-open", opening);
});
navigation.addEventListener("click", event => {
  if (!event.target.closest("a")) return;
  menuButton.setAttribute("aria-expanded", "false");
  menuButton.setAttribute("aria-label", "Open navigation");
  navigation.classList.remove("is-open");
});

const isLocalPreview = location.protocol === "file:" || location.pathname.split("/").includes("website");
if (!isLocalPreview) {
  const releaseBase = "https://github.com/deepak-c04/verci-website/releases/download/aurafy-preview-2026-11-21-2.2.19-build-43/";
  document.querySelectorAll('a[href^="../dist/"]').forEach(link => {
    const filename = link.getAttribute("href").split("/").pop();
    link.href = releaseBase + encodeURIComponent(filename);
    link.removeAttribute("download");
  });
}

document.querySelectorAll("a[href^='#']").forEach(link => {
  link.addEventListener("click", event => {
    const target = document.querySelector(link.getAttribute("href"));
    if (!target) return;
    event.preventDefault();
    const targetHeading = target.matches("h1, h2") ? target : target.querySelector("h1, h2");
    if (targetHeading) {
      targetHeading.tabIndex = -1;
      targetHeading.focus({ preventScroll: true });
    }
    target.scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start" });
    history.replaceState(null, "", link.getAttribute("href"));
  });
});

const demoVisualizer = document.querySelector(".visualizer-card");
if (demoVisualizer) {
  const moodButtons = [...demoVisualizer.querySelectorAll("[data-mood]")];
  const moods = ["glow", "daydream", "after-hours"];
  moodButtons.forEach(button => {
    button.addEventListener("click", () => {
      const mood = button.dataset.mood;
      if (!moods.includes(mood)) return;
      demoVisualizer.classList.remove(...moods.map(name => `mood-${name}`));
      demoVisualizer.classList.add(`mood-${mood}`);
      moodButtons.forEach(option => {
        const selected = option === button;
        option.classList.toggle("is-selected", selected);
        option.setAttribute("aria-pressed", String(selected));
      });
    });
  });

  const lyricRegion = demoVisualizer.querySelector(".lyric-illustration");
  const lyricNodes = {
    before: lyricRegion.querySelector('[data-demo-lyric="before"]'),
    focus: lyricRegion.querySelector('[data-demo-lyric="focus"]'),
    after: lyricRegion.querySelector('[data-demo-lyric="after"]'),
  };
  const minutesNode = demoVisualizer.querySelector("[data-demo-minutes]");
  const secondsNode = demoVisualizer.querySelector("[data-demo-seconds]");
  const lyricFrames = [
    { before: "let the", focus: "feeling", after: "find you" },
    { before: "stay with", focus: "this moment", after: "a little longer" },
    { before: "move like", focus: "moonlight", after: "through the dark" },
    { before: "keep your", focus: "soft glow", after: "close to you" },
  ];
  const motionPreference = window.matchMedia("(prefers-reduced-motion: reduce)");
  let frameIndex = 0;
  let visualizerSeconds = 222;
  let lyricTimer = 0;
  let clockTimer = 0;
  let firstLyricTimer = 0;

  function stopPreview() {
    window.clearInterval(lyricTimer);
    window.clearInterval(clockTimer);
    window.clearTimeout(firstLyricTimer);
    lyricTimer = 0;
    clockTimer = 0;
    firstLyricTimer = 0;
  }

  function advanceLyrics() {
    lyricRegion.classList.add("is-changing");
    window.setTimeout(() => {
      frameIndex = (frameIndex + 1) % lyricFrames.length;
      const nextFrame = lyricFrames[frameIndex];
      for (const [key, node] of Object.entries(lyricNodes)) node.textContent = nextFrame[key];
      lyricRegion.classList.remove("is-changing");
    }, 240);
  }

  function startPreview() {
    if (motionPreference.matches || document.hidden || lyricTimer) return;
    firstLyricTimer = window.setTimeout(advanceLyrics, 900);
    lyricTimer = window.setInterval(advanceLyrics, 2800);
    clockTimer = window.setInterval(() => {
      visualizerSeconds = (visualizerSeconds + 1) % 3600;
      minutesNode.textContent = String(Math.floor(visualizerSeconds / 60)).padStart(2, "0");
      secondsNode.textContent = String(visualizerSeconds % 60).padStart(2, "0");
    }, 1000);
  }

  function syncPreviewState() {
    stopPreview();
    startPreview();
  }

  startPreview();
  document.addEventListener("visibilitychange", syncPreviewState);
  motionPreference.addEventListener("change", syncPreviewState);
}
