// Results rows: clicking anywhere on a row opens that cell's drill-down page. Real links and
// buttons inside the row keep their own behaviour, and each row still has in-cell links (app name,
// result) so keyboard and no-JS navigation work without this.
document.addEventListener("click", (event) => {
  if (event.target.closest("a, button")) return;
  const row = event.target.closest("tr.row-link");
  if (row && row.dataset.href) window.location.href = row.dataset.href;
});

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
