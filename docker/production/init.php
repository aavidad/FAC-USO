<?php
/** Preparación inicial por CLI de esta instalación, nunca un endpoint HTTP. */
declare(strict_types=1);
if (PHP_SAPI !== 'cli' || getenv('FACUSO_DOMAIN') !== 'facuso.cidonia.cloud') exit(1);
define('WP_INSTALLING', true);
define('FS_METHOD', 'direct');
$_SERVER['HTTP_HOST'] = 'facuso.cidonia.cloud';
$_SERVER['HTTPS'] = 'on';
$_SERVER['REQUEST_URI'] = '/';
require '/var/www/html/wp-load.php';
if (!defined('WP_HOME') || WP_HOME !== 'https://facuso.cidonia.cloud' || wp_get_environment_type() !== 'staging') {
    throw new RuntimeException('Destino no autorizado.');
}
require_once ABSPATH . 'wp-admin/includes/upgrade.php';
require_once ABSPATH . 'wp-admin/includes/plugin.php';
require_once ABSPATH . 'wp-admin/includes/file.php';
add_filter('pre_wp_mail', '__return_true', PHP_INT_MAX);
if (!is_blog_installed()) {
    $password = trim(file_get_contents('/run/secrets/admin_password'));
    if (strlen($password) < 32) throw new RuntimeException('Secreto administrador inválido.');
    $result = wp_install('FAC-USO Andalucía', 'facuso-admin', 'facuso-admin@example.invalid', false, '', $password, 'es_ES');
    unset($password);
    if (is_wp_error($result)) throw new RuntimeException($result->get_error_message());
    foreach (get_posts(['post_type'=>['page','post'],'post_status'=>'any','numberposts'=>-1]) as $post) {
        wp_delete_post($post->ID, true);
    }
}
$admin = get_user_by('login', 'facuso-admin');
if (!$admin || !in_array('administrator', $admin->roles, true)) throw new RuntimeException('Administrador inesperado.');
wp_set_current_user($admin->ID);
update_option('blog_public', '0');
update_option('timezone_string', 'Europe/Madrid');
update_option('WPLANG', 'es_ES');
update_option('date_format', 'j F Y');
WP_Filesystem();
if (!is_file(WP_PLUGIN_DIR . '/facuso-arranque/facuso-arranque.php')) {
    $result = unzip_file('/import/facuso-arranque.zip', WP_PLUGIN_DIR);
    if (is_wp_error($result)) throw new RuntimeException($result->get_error_message());
}
$result = activate_plugin('facuso-arranque/facuso-arranque.php');
if (is_wp_error($result)) throw new RuntimeException($result->get_error_message());
require_once WP_PLUGIN_DIR . '/facuso-arranque/facuso-arranque.php';
global $wp_rewrite;
$wp_rewrite->set_permalink_structure('/%postname%/');
$wp_rewrite->flush_rules(true);
echo wp_json_encode(facuso_import(true), JSON_UNESCAPED_UNICODE), PHP_EOL;
echo wp_json_encode(['url'=>home_url(),'pages'=>(int)wp_count_posts('page')->publish,'posts'=>(int)wp_count_posts('post')->publish]), PHP_EOL;
