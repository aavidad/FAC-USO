<?php
// Actualiza exclusivamente las páginas de muestra creadas en este Docker local.
$_SERVER['HTTP_HOST'] = '127.0.0.1:18086';
require '/var/www/html/wp-load.php';
if (wp_get_environment_type() !== 'local' || get_option('home') !== 'http://127.0.0.1:18086') {
    throw new RuntimeException('Solo se admite la muestra local.');
}
wp_set_current_user(get_user_by('login', 'facuso-admin')->ID);
$data = facuso_data();
$ids = [];
foreach ($data['pages'] as $item) {
    $page = get_page_by_path($item['path'], OBJECT, 'page');
    if (!$page || get_post_meta($page->ID, '_facuso_key', true) !== $item['slug']) {
        throw new RuntimeException('Falta una página propia de la muestra: ' . $item['slug']);
    }
    $ids[$item['slug']] = $page->ID;
}
foreach ($data['pages'] as $item) {
    $content = preg_replace_callback('/\[\[page:([a-z0-9-]+)\]\]/', fn($m) => esc_url(get_permalink($ids[$m[1]])), $item['html']);
    $content = preg_replace_callback('/\[\[asset:([a-z0-9.\/-]+)\]\]/', fn($m) => esc_url(plugins_url('theme/assets/' . $m[1], WP_PLUGIN_DIR . '/facuso-arranque/facuso-arranque.php')), $content);
    wp_update_post(['ID' => $ids[$item['slug']], 'post_content' => wp_kses_post($content)]);
    update_post_meta($ids[$item['slug']], '_facuso_sources', $item['sources']);
}
echo wp_json_encode(facuso_import(true), JSON_UNESCAPED_UNICODE) . "\n";
