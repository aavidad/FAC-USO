<?php
/** Ensayo local del comportamiento de enlaces en el WordPress de Docker. */
require_once '/var/www/html/wp-load.php';

if (!function_exists('facuso_external_link_kind')) {
    require_once WP_PLUGIN_DIR . '/facuso-arranque/includes/external-links.php';
}

$checks = 0;
$check = static function ($actual, $expected, string $message) use (&$checks): void {
    $checks++;
    if ($actual !== $expected) {
        throw new RuntimeException($message . ': esperado ' . var_export($expected, true) . ', obtenido ' . var_export($actual, true));
    }
};

$home = wp_parse_url(home_url('/'));
$host = $home['host'];
$scheme = $home['scheme'];
$authority = $host . (isset($home['port']) ? ':' . $home['port'] : '');
$origin = $scheme . '://' . $authority;
$internal = $origin . '/portal/noticia?tipo=1#fuente';

foreach ([
    'https://uso.es' => true,
    '//boe.es/diario_boe/' => true,
    $internal => false,
    ($scheme === 'https' ? 'http' : 'https') . '://' . $authority . '/portal/noticia' => true,
    $scheme . '://' . $host . ':' . ((int) ($home['port'] ?? ($scheme === 'https' ? 443 : 80)) + 1) . '/portal/noticia' => true,
    '/portal/noticia?tipo=1#fuente' => false,
    '?tipo=1#fuente' => false,
    '#fuente' => null,
    'mailto:info@example.org' => null,
    'tel:+34900000000' => null,
    'javascript:alert(1)' => null,
] as $url => $expected) {
    $check(facuso_external_link_kind($url), $expected, 'Clasificación ' . $url);
}

$html = '<a id="outside" href="https://uso.es" rel="ugc nofollow">USO</a>'
    . '<a id="protocol" href="//boe.es">BOE</a>'
    . '<A id="inside" href="' . esc_attr($internal) . '" target="_blank">Interno</A>'
    . '<a id="relative" href="/portal/noticia?tipo=1#fuente" target="_blank">Ruta</a>'
    . '<a id="mail" href="mailto:info@example.org">Correo</a>'
    . '<a id="phone" href="tel:+34900000000">Teléfono</a>'
    . '<a id="hash" href="#fuente">Ancla</a>'
    . '<a id="scheme" href="javascript:alert(1)">Esquema</a>';
$processed = apply_filters('the_content', $html);
$links = [];
$processor = new WP_HTML_Tag_Processor($processed);
while ($processor->next_tag(['tag_name' => 'A'])) {
    $links[$processor->get_attribute('id')] = [
        'target' => $processor->get_attribute('target'),
        'rel' => (string) $processor->get_attribute('rel'),
    ];
}
$check($links['outside']['target'], '_blank', 'Contenido externo');
$check($links['outside']['rel'], 'ugc nofollow noopener noreferrer', 'Relaciones existentes');
$check($links['protocol']['target'], '_blank', 'URL sin protocolo');
$check($links['inside']['target'], null, 'URL absoluta interna');
$check($links['relative']['target'], null, 'Ruta interna');
foreach (['mail', 'phone', 'hash', 'scheme'] as $id) {
    $check($links[$id]['target'], null, 'Esquema intacto ' . $id);
}
$check(facuso_external_link_attributes('https://uso.es'), ' target="_blank" rel="noopener noreferrer"', 'Atributos manuales externos');
$check(facuso_external_link_attributes($internal), '', 'Atributos manuales internos');

$menu = apply_filters('nav_menu_link_attributes', ['href' => 'https://uso.es', 'rel' => 'sponsored'], null, null, 0);
$check($menu['target'], '_blank', 'Menú externo');
$check($menu['rel'], 'sponsored noopener noreferrer', 'Menú conserva rel');
$menu = apply_filters('nav_menu_link_attributes', ['href' => $internal, 'target' => '_blank'], null, null, 0);
$check(isset($menu['target']), false, 'Menú interno');

require_once ABSPATH . 'wp-admin/includes/class-wp-screen.php';
require_once ABSPATH . 'wp-admin/includes/screen.php';
set_current_screen('dashboard');
$check(facuso_external_links_public_request(), false, 'Administración excluida');
$admin_content = apply_filters('the_content', '<a href="https://uso.es">USO</a>');
$admin_processor = new WP_HTML_Tag_Processor($admin_content);
$admin_processor->next_tag(['tag_name' => 'A']);
$check($admin_processor->get_attribute('target'), null, 'Contenido administrativo intacto');

echo "Enlaces externos: {$checks} comprobaciones correctas.\n";
