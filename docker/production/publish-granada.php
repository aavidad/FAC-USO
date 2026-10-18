<?php
/** Actualización acotada de una página propia; invocación CLI, nunca HTTP. */
declare(strict_types=1);
if (PHP_SAPI !== 'cli' || getenv('FACUSO_DOMAIN') !== 'facuso.cidonia.cloud') exit(1);
$_SERVER['HTTPS'] = 'on';
require '/var/www/html/wp-load.php';
if (home_url() !== 'https://facuso.cidonia.cloud' || wp_get_environment_type() !== 'staging') exit(1);
$admin = get_user_by('login', 'facuso-admin');
if (!$admin || !in_array('administrator', $admin->roles, true)) exit(1);
wp_set_current_user($admin->ID);
$page = get_page_by_path('territorios/granada/diputacion-de-granada');
if (!$page || get_post_meta($page->ID, '_facuso_key', true) !== 'diputacion-de-granada') throw new RuntimeException('Página ajena al paquete.');
$item = null;
foreach (facuso_data()['pages'] as $candidate) if ($candidate['slug'] === 'diputacion-de-granada') $item = $candidate;
if (!$item || !str_contains($item['html'], '[facuso_muestra_tcae]')) throw new RuntimeException('Manifiesto inesperado.');
$content = preg_replace_callback('/\[\[asset:([a-z0-9.\/-]+)\]\]/', fn($m) => esc_url(plugins_url('theme/assets/' . $m[1], WP_PLUGIN_DIR . '/facuso-arranque/facuso-arranque.php')), $item['html']);
wp_save_post_revision($page->ID);
$id = wp_update_post(['ID'=>$page->ID, 'post_content'=>wp_kses_post($content)], true);
if (is_wp_error($id)) throw new RuntimeException($id->get_error_message());
update_post_meta($id, '_facuso_sources', $item['sources']);
echo wp_json_encode(['updated_page'=>$id, 'url'=>get_permalink($id)], JSON_UNESCAPED_SLASHES), PHP_EOL;
