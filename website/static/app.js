// Chart legends: clicking a cloud hides or shows its line in that chart.
document.addEventListener("click", (event) => {
  const button = event.target.closest(".legend-item");
  if (!button) return;
  const chart = button.closest("[data-chart]");
  const visible = button.getAttribute("aria-pressed") !== "false";
  button.setAttribute("aria-pressed", String(!visible));
  for (const series of chart.querySelectorAll("g.series")) {
    if (series.dataset.series === button.dataset.series) series.classList.toggle("is-hidden", visible);
  }
});
