document.addEventListener("htmx:afterSwap", (event) => {
  const target = event.detail && event.detail.target;
  if (!target) return;
  target.classList.add("flash");
  window.setTimeout(() => target.classList.remove("flash"), 420);
});
