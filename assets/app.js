(function(){
  const toggle=document.querySelector('[data-menu-toggle]');
  const nav=document.querySelector('[data-nav]');
  if(toggle&&nav){toggle.addEventListener('click',()=>{const open=nav.classList.toggle('is-open');toggle.setAttribute('aria-expanded',String(open));});}
  const search=document.querySelector('[data-paper-search]');
  const filter=document.querySelector('[data-theme-filter]');
  const cards=Array.from(document.querySelectorAll('[data-paper-card]'));
  const status=document.querySelector('[data-result-status]');
  if(!search||!filter||!cards.length)return;
  function update(){
    const q=search.value.toLocaleLowerCase().trim();const theme=filter.value;let visible=0;
    for(const card of cards){const matchesText=!q||(card.dataset.search||'').includes(q);const matchesTheme=!theme||card.dataset.theme===theme;const ok=matchesText&&matchesTheme;card.hidden=!ok;card.style.display=ok?'':'none';if(ok)visible++;}
    if(status)status.textContent=visible+' of '+cards.length+' selected papers shown';
  }
  search.addEventListener('input',update);filter.addEventListener('change',update);update();
})();
