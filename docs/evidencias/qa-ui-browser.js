async page => {
  const base = 'http://127.0.0.1:18086';
  const errors = [];
  const pageErrors = [];
  page.on('pageerror', error => pageErrors.push(error.message));
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto(base + '/', { waitUntil: 'domcontentloaded' });
  const desktop = await page.evaluate(() => ({
    overflow: document.documentElement.scrollWidth - innerWidth,
    blocks: [...document.querySelectorAll('.fac-news')].map(section => ({
      cards: section.querySelectorAll('.fac-card').length,
      photos: section.querySelectorAll('.fac-card-photo img').length,
      filters: section.querySelectorAll('.fac-filters').length,
    })),
  }));
  if (desktop.overflow > 1) errors.push('Desbordamiento en portada escritorio');
  if (desktop.blocks.length !== 2 || desktop.blocks.some(block => block.cards !== 6 || block.photos !== 6))
    errors.push('Portada escritorio sin dos bloques de seis noticias con foto');
  await page.screenshot({ path: 'docs/evidencias/qa-inicio-escritorio.png', type: 'png' });

  await page.setViewportSize({ width: 390, height: 844 });
  await page.reload({ waitUntil: 'domcontentloaded' });
  await page.screenshot({ path: 'docs/evidencias/qa-inicio-movil.png', type: 'png' });
  await page.locator('.fac-news').nth(1).scrollIntoViewIfNeeded();
  await page.locator('.fac-news').nth(1).locator('img').evaluateAll(async images => {
    for (const image of images) {
      image.loading = 'eager';
      await image.decode();
    }
  });
  await page.locator('.fac-news').nth(1).screenshot({ path: 'docs/evidencias/qa-empleo-movil.png', type: 'png' });
  const mobile = await page.evaluate(() => ({
    overflow: document.documentElement.scrollWidth - innerWidth,
    employmentImages: [...document.querySelectorAll('.fac-news')][1]
      ? [...document.querySelectorAll('.fac-news')[1].querySelectorAll('.fac-card-photo img')].map(img => img.naturalWidth) : [],
  }));
  if (mobile.overflow > 1) errors.push('Desbordamiento en portada móvil');
  if (mobile.employmentImages.length !== 6 || mobile.employmentImages.some(width => width === 0))
    errors.push('Fotografías de empleo no cargan al desplazarse en móvil');

  await page.goto(base + '/fotos/', { waitUntil: 'domcontentloaded' });
  const gallery = await page.evaluate(() => ({
    overflow: document.documentElement.scrollWidth - innerWidth,
    photos: document.querySelectorAll('.fac-photo-gallery img').length,
    captions: document.querySelectorAll('.fac-photo-gallery figcaption').length,
    montage: document.querySelector('.fac-section-photo figcaption')?.textContent || '',
  }));
  if (gallery.overflow > 1 || gallery.photos !== 25 || gallery.captions !== 25 || !gallery.montage.includes('IA'))
    errors.push('Galería móvil incompleta o desbordada');
  await page.screenshot({ path: 'docs/evidencias/qa-galeria-movil.png', type: 'png' });

  for (const slug of [
    'facuso-granada-786951a81428af8f1d57db00',
    'spj-uso-andalucia-marca-la-hoja-de-ruta-para-la-subida-retributiva-del-personal-de-justicia',
  ]) {
    const response = await page.goto(`${base}/${slug}/`, { waitUntil: 'domcontentloaded' });
    if (!response || response.status() !== 200) errors.push(`Noticia de ejemplo rota: ${slug}`);
    const result = await page.evaluate(() => ({
      photo: !!document.querySelector('main .fac-article-photo img'),
      caption: !!document.querySelector('main .fac-article-photo figcaption'),
      overflow: document.documentElement.scrollWidth - innerWidth,
    }));
    if (!result.photo || !result.caption || result.overflow > 1) errors.push(`Noticia visual incompleta: ${slug}`);
  }
  return { desktop, mobile, gallery: { overflow: gallery.overflow, photos: gallery.photos, captions: gallery.captions, montageLabeled: gallery.montage.includes('IA') }, pageErrors: [...new Set(pageErrors)], errors };
}
