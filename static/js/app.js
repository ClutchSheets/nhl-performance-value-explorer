function renderChart(id, fig){
  const el = document.getElementById(id);
  if(!el) return;
  Plotly.newPlot(el, fig.data, fig.layout, {responsive:true, displayModeBar:false});
}

document.addEventListener('click', function(e){
  const th = e.target.closest('th');
  if(!th || !th.closest('table.sortable')) return;
  const table = th.closest('table');
  const idx = Array.from(th.parentNode.children).indexOf(th);
  const rows = Array.from(table.tBodies[0].rows);
  const asc = th.dataset.asc !== 'true';
  rows.sort((a,b)=>{
    const av = a.cells[idx].innerText.replace(/[$,]/g,'');
    const bv = b.cells[idx].innerText.replace(/[$,]/g,'');
    const an = parseFloat(av), bn = parseFloat(bv);
    if(!Number.isNaN(an) && !Number.isNaN(bn)) return asc ? an-bn : bn-an;
    return asc ? av.localeCompare(bv) : bv.localeCompare(av);
  });
  th.dataset.asc = asc;
  rows.forEach(r=>table.tBodies[0].appendChild(r));
});
