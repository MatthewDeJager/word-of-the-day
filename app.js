(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const els = {
    word: $("word"),
    pronunciation: $("pronunciation"),
    pos: $("pos"),
    definition: $("definition"),
    example: $("example"),
    synonymsRow: $("synonymsRow"),
    synonyms: $("synonyms"),
    button: $("newWord"),
  };

  let words = [];
  let last = -1;

  // Sets text and hides the element entirely when there is nothing to show.
  function setOptional(el, text, row = el) {
    el.textContent = text || "";
    row.hidden = !text;
  }

  function render(w) {
    els.word.textContent = w.word;
    setOptional(els.pronunciation, w.pronunciation);
    els.pos.textContent = w.pos;
    els.definition.textContent = w.definition;
    setOptional(els.example, w.example ? "“" + w.example + "”" : "");
    setOptional(els.synonyms, (w.synonyms || []).join(", "), els.synonymsRow);
  }

  function pick() {
    if (!words.length) return;
    let i = Math.floor(Math.random() * words.length);
    if (words.length > 1 && i === last) i = (i + 1) % words.length;
    last = i;
    render(words[i]);
  }

  function showError(message) {
    els.word.textContent = "—";
    els.pos.textContent = "";
    els.definition.textContent = message;
    els.button.disabled = true;
  }

  els.button.addEventListener("click", pick);
  window.addEventListener("keydown", (e) => {
    if (e.code !== "Space" || e.repeat || e.ctrlKey || e.metaKey || e.altKey) return;
    // A focused button already fires "click" on space; don't double-roll.
    if (e.target === els.button) return;
    e.preventDefault();
    pick();
  });

  fetch("words.json")
    .then((res) => {
      if (!res.ok) throw new Error("HTTP " + res.status);
      return res.json();
    })
    .then((data) => {
      words = Array.isArray(data)
        ? data.filter((w) => w && w.word && w.pos && w.definition)
        : [];
      if (!words.length) throw new Error("no words");
      els.button.disabled = false;
      pick();
    })
    .catch(() => {
      showError(
        location.protocol === "file:"
          ? "Couldn't load words.json over file://. Run `python -m http.server` and open http://localhost:8000."
          : "Couldn't load the word list. Check your connection and reload."
      );
    });

  // Service worker: offline support + reload once when a new version takes over.
  if ("serviceWorker" in navigator && location.protocol !== "file:") {
    const hadController = !!navigator.serviceWorker.controller;
    let reloaded = false;
    navigator.serviceWorker.addEventListener("controllerchange", () => {
      // Skip the very first install (nothing stale on screen to replace).
      if (!hadController || reloaded) return;
      reloaded = true;
      location.reload();
    });
    window.addEventListener("load", () => {
      navigator.serviceWorker.register("service-worker.js").catch(() => {});
    });
  }
})();
