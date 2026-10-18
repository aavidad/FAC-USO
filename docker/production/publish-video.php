<?php
/** Actualiza exclusivamente la página propia de Vídeos; nunca un endpoint web. */
declare(strict_types=1);
if (PHP_SAPI !== 'cli' || getenv('FACUSO_DOMAIN') !== 'facuso.cidonia.cloud') exit(1);
$_SERVER['HTTPS'] = 'on';
require '/var/www/html/wp-load.php';
if (home_url() !== 'https://facuso.cidonia.cloud' || wp_get_environment_type() !== 'staging') exit(1);
$admin = get_user_by('login', 'facuso-admin');
if (!$admin || !in_array('administrator', $admin->roles, true)) exit(1);
wp_set_current_user($admin->ID);
$page = get_page_by_path('conocenos/videos');
if (!$page || get_post_meta($page->ID, '_facuso_key', true) !== 'videos') {
    throw new RuntimeException('No se modifica una página que no pertenezca al paquete.');
}
$item = null;
foreach (facuso_data()['pages'] as $candidate) {
    if ($candidate['slug'] === 'videos') $item = $candidate;
}
if (!$item || !str_contains($item['html'], '/facuso-presentacion/facuso-recorrido-v3.mp4')) {
    throw new RuntimeException('El manifiesto no contiene el recorrido corregido.');
}
$video = '/var/www/html/wp-content/uploads/facuso-presentacion/facuso-recorrido-v3.mp4';
if (!is_file($video) || filesize($video) < 1000000 || is_link($video)) {
    throw new RuntimeException('Falta el MP4 publicado.');
}
// Conserva una revisión recuperable de la página antes de actualizarla.
wp_save_post_revision($page->ID);
$id = wp_update_post(['ID'=>$page->ID, 'post_content'=>wp_kses_post($item['html'])], true);
if (is_wp_error($id)) throw new RuntimeException($id->get_error_message());
echo wp_json_encode(['updated_page'=>$id, 'url'=>get_permalink($id),
    'video_bytes'=>filesize($video)], JSON_UNESCAPED_SLASHES), PHP_EOL;
