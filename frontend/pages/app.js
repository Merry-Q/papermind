const list = document.getElementById('documents');
const frame = document.getElementById('reading');
const title = document.getElementById('reading-title');
const meta = document.getElementById('reading-meta');
const count = document.getElementById('count');
const search = document.getElementById('search');
let catalog = [], selected = '';

function renderList() {
  const query = search.value.trim().toLocaleLowerCase();
  const matches = catalog.filter(doc => (doc.title + ' ' + doc.readingTitle).toLocaleLowerCase().includes(query));
  list.replaceChildren();
  count.textContent = query ? `${matches.length} / ${catalog.length} 篇文献` : `${catalog.length} 篇文献 · 已生成交互讲解`;
  for (const doc of matches) {
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = doc.title;
    button.dataset.document = doc.id;
    button.setAttribute('aria-current', String(doc.id === selected));
    const detail = document.createElement('small');
    detail.textContent = `${doc.pages} 页 · 交互讲解`;
    button.append(detail);
    button.addEventListener('click', () => openDocument(doc.id));
    list.append(button);
  }
}

function openDocument(id, replace = false) {
  const doc = catalog.find(item => item.id === id) || catalog[0];
  selected = doc.id;
  title.textContent = doc.readingTitle;
  meta.textContent = `${doc.pages} 页原文 · 交互图表与引用可直接探索`;
  document.title = `${doc.title} · paperMind`;
  frame.src = doc.reading;
  frame.hidden = false;
  for (const [key, href] of [['pdf-link', doc.pdf], ['reading-link', doc.reading]]) {
    const link = document.getElementById(key);
    link.href = href;
    link.hidden = false;
  }
  const url = new URL(location.href);
  url.searchParams.set('document', doc.id);
  if (replace) history.replaceState(null, '', url);
  else history.pushState(null, '', url);
  renderList();
}

search.addEventListener('input', renderList);
window.addEventListener('popstate', () => { if (catalog.length) openDocument(new URLSearchParams(location.search).get('document'), true); });
try {
  const response = await fetch('./catalog.json');
  if (!response.ok) throw new Error('文献目录加载失败，请刷新重试。');
  catalog = await response.json();
  if (!catalog.length) throw new Error('尚无已发布的交互讲解。');
  openDocument(new URLSearchParams(location.search).get('document'), true);
} catch (error) {
  title.textContent = '文献暂时无法打开';
  count.textContent = '加载失败';
  const box = document.getElementById('error');
  box.textContent = error.message;
  box.hidden = false;
}
