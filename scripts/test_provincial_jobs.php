<?php
/** Ensayo de navegación y selección provincial en la muestra aislada. */
$_SERVER['HTTP_HOST'] = '127.0.0.1:18086';
require '/var/www/html/wp-load.php';
if (wp_get_environment_type() !== 'local') {
    throw new RuntimeException('Las pruebas requieren el WordPress local.');
}
$checks = 0;
$assert = function (bool $value, string $message) use (&$checks): void {
    $checks++;
    if (!$value) {
        throw new RuntimeException($message);
    }
};
$source_ids = function (string $province, array $get = []): array {
    $_GET = $get;
    $page = get_page_by_path('territorios/' . $province . '/empleo-publico-' . $province, OBJECT, 'page');
    $GLOBALS['post'] = $page;
    setup_postdata($page);
    $html = do_shortcode($page->post_content);
    $document = new DOMDocument();
    @$document->loadHTML('<?xml encoding="UTF-8">' . $html, LIBXML_NONET);
    $xpath = new DOMXPath($document);
    $ids = [];
    foreach ($xpath->query('//article[contains(@class,"fac-card")]//h3/a/@href') as $href) {
        $ids[] = url_to_postid($href->value);
    }
    return $ids;
};
$results = [];
foreach (['almeria','cadiz','cordoba','granada','huelva','jaen','malaga','sevilla'] as $province) {
    $page = get_page_by_path('territorios/' . $province . '/empleo-publico-' . $province, OBJECT, 'page');
    $assert($page instanceof WP_Post && $page->post_status === 'publish', 'Falta el empleo provincial: ' . $province);
    $ids = $source_ids($province);
    $results[$province] = count($ids);
    foreach ($ids as $id) {
        $assert($id > 0, 'Enlace de noticia sin destino');
        $assert(in_array($province, wp_get_post_categories($id, ['fields'=>'slugs']), true), 'Noticia fuera de provincia');
        $source = get_post_meta($id, 'facuso_source_url', true);
        $assert((bool) preg_match('~' . facuso_source_pattern('bop', $province) . '~i', $source), 'Noticia ajena al BOP de ' . $province);
    }
    if ($province !== 'malaga') {
        $assert(count($ids) > 0, 'Faltan anuncios del boletín: ' . $province);
    }
}
$baseline = $source_ids('almeria');
$assert(count($baseline) >= 7, 'Faltan los siete anuncios del lector BOP Almería');
$assert($source_ids('almeria', ['fac_territorio'=>'sevilla']) === $baseline, 'GET cambió la provincia fijada');
$assert($source_ids('almeria', ['fac_materia'=>'formacion']) === $baseline, 'GET cambió la materia fijada');
$assert($source_ids('almeria', ['fac_fuente'=>['boe']]) === $baseline, 'Una fuente array alteró la selección');
$assert($source_ids('almeria', ['fac_fuente'=>'bop.*']) === $baseline, 'Una fuente inválida alteró la selección');
$boe = $source_ids('almeria', ['fac_fuente'=>'boe','fac_territorio'=>'sevilla']);
$assert(count($boe) > 0, 'No se puede consultar el BOE complementario');
foreach ($boe as $id) {
    $assert(in_array('almeria', wp_get_post_categories($id, ['fields'=>'slugs']), true), 'El BOE perdió la provincia');
    $assert((bool) preg_match('~' . facuso_source_pattern('boe') . '~i', get_post_meta($id,'facuso_source_url',true)), 'Fuente BOE incorrecta');
}
foreach (['https://app.dipalme.org.ejemplo.invalid/bop/','https://ejemplo.invalid/?next=https://app.dipalme.org/bop/','https://app.dipalme.org@ejemplo.invalid/bop/','https://www.bopcadiz.es/documento.pdf'] as $fake) {
    $assert(!preg_match('~' . facuso_source_pattern('bop','almeria') . '~i', $fake), 'Patrón de fuente demasiado amplio');
}
$_GET = [];
echo wp_json_encode(['checks'=>$checks,'errors'=>0,'bop_cards_first_page'=>$results,'almeria_boe_cards'=>count($boe)], JSON_UNESCAPED_UNICODE) . "\n";
