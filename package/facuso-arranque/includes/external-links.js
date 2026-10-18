(() => {
  'use strict';

  let homeOrigin;
  try {
    homeOrigin = new URL(window.facusoExternalLinksHome).origin;
  } catch (_) {
    return;
  }

  const update = (link) => {
    const href = link.getAttribute('href');
    if (!href || href.trim().startsWith('#')) return;

    let url;
    try {
      url = new URL(href, window.location.href);
    } catch (_) {
      return;
    }
    if (url.protocol !== 'http:' && url.protocol !== 'https:') return;

    if (url.origin === homeOrigin) {
      if (link.hasAttribute('target')) link.removeAttribute('target');
      return;
    }
    if (link.getAttribute('target') !== '_blank') link.setAttribute('target', '_blank');
    const relations = new Set((link.getAttribute('rel') || '').split(/\s+/).filter(Boolean));
    relations.add('noopener');
    relations.add('noreferrer');
    const rel = Array.from(relations).join(' ');
    if (link.getAttribute('rel') !== rel) link.setAttribute('rel', rel);
  };

  const scan = (node) => {
    if (node.nodeType !== 1) return;
    if (node.matches('a[href]')) update(node);
    node.querySelectorAll('a[href]').forEach(update);
  };

  scan(document.documentElement);
  new MutationObserver((changes) => {
    changes.forEach((change) => {
      if (change.type === 'attributes') {
        update(change.target);
      } else {
        change.addedNodes.forEach(scan);
      }
    });
  }).observe(document.documentElement, {
    subtree: true,
    childList: true,
    attributes: true,
    attributeFilter: ['href', 'target', 'rel']
  });

  document.addEventListener('click', (event) => {
    const link = event.target.closest && event.target.closest('a[href]');
    if (link) update(link);
  }, true);
})();
