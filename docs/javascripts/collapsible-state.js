/* Persist the user's open/closed preference for documentation disclosures. */
(() => {
  "use strict";

  const storagePrefix = "pyinfra-doc-details:";
  let restoring = false;

  function getDetailsKey(details) {
    const page = window.location.pathname;
    const disclosures = Array.from(
      document.querySelectorAll(".md-content details")
    );
    const index = disclosures.indexOf(details);

    if (index < 0) {
      return null;
    }

    const summary = details.querySelector("summary");
    const label = summary ? summary.textContent.trim() : "";

    return storagePrefix + encodeURIComponent(
      page + ":" + index + ":" + label
    );
  }

  function restoreDisclosureStates() {
    const disclosures = document.querySelectorAll(".md-content details");
    restoring = true;

    disclosures.forEach((details) => {
      const key = getDetailsKey(details);

      if (!key) {
        return;
      }

      try {
        const savedState = window.localStorage.getItem(key);

        if (savedState === "open" || savedState === "closed") {
          details.open = savedState === "open";
        }
      } catch (_error) {
        // Keep disclosures usable when browser storage is unavailable.
      }
    });

    restoring = false;
  }

  document.addEventListener("toggle", (event) => {
    if (restoring || !(event.target instanceof HTMLDetailsElement)) {
      return;
    }

    const key = getDetailsKey(event.target);

    if (!key) {
      return;
    }

    try {
      window.localStorage.setItem(key, event.target.open ? "open" : "closed");
    } catch (_error) {
      // Toggling remains functional when browser storage is unavailable.
    }
  }, true);

  restoreDisclosureStates();

  if (window.document$ && typeof window.document$.subscribe === "function") {
    window.document$.subscribe(restoreDisclosureStates);
  }
})();
