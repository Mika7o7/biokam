const lists = document.querySelectorAll('.gallery'); 

lists.forEach(el => {
  const listItems = el.querySelectorAll('li');
  const n = Math.ceil(el.children.length / 2);
  el.style.setProperty('--total', n);
});