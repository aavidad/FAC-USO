<?php
// Solo se ejecuta en el contenedor local de pruebas y sobre su volumen desechable.
define('WP_INSTALLING', true);
$_SERVER['HTTP_HOST'] = '127.0.0.1:18086';
$_SERVER['REQUEST_URI'] = '/';
require '/var/www/html/wp-load.php';
if (wp_get_environment_type() !== 'local') {
    throw new RuntimeException('Este guion requiere el entorno local.');
}
require_once ABSPATH . 'wp-admin/includes/upgrade.php';
require_once ABSPATH . 'wp-admin/includes/plugin.php';
require_once ABSPATH . 'wp-admin/includes/file.php';
if (!is_blog_installed()) {
    wp_install('FAC-USO Andalucía', 'facuso-admin', 'equipo@example.invalid', false, '', trim(file_get_contents('/run/secrets/admin_password')), 'es_ES');
    update_option('siteurl', 'http://127.0.0.1:18086');
    update_option('home', 'http://127.0.0.1:18086');
    update_option('blog_public', '0');
    update_option('timezone_string', 'Europe/Madrid');
    update_option('date_format', 'j F Y');
    // Quita únicamente los contenidos de muestra de esta instalación recién creada.
    foreach (get_posts(['post_type' => ['page', 'post'], 'post_status' => 'any', 'numberposts' => -1]) as $post) {
        wp_delete_post($post->ID, true);
    }
}
wp_set_current_user(get_user_by('login', 'facuso-admin')->ID);
WP_Filesystem();
$result = unzip_file('/importacion/facuso-arranque.zip', WP_PLUGIN_DIR);
if (is_wp_error($result)) {
    throw new RuntimeException($result->get_error_message());
}
$result = activate_plugin('facuso-arranque/facuso-arranque.php');
if (is_wp_error($result)) {
    throw new RuntimeException($result->get_error_message());
}
if (in_array('--refresh-theme', $argv, true) && is_file(get_theme_root() . '/facuso-andalucia/facuso-theme.marker')) {
    $result = copy_dir(WP_PLUGIN_DIR . '/facuso-arranque/theme', get_theme_root() . '/facuso-andalucia');
    if (is_wp_error($result)) {
        throw new RuntimeException($result->get_error_message());
    }
}
global $wp_rewrite;
$wp_rewrite->set_permalink_structure('/%postname%/');
$wp_rewrite->flush_rules(true);
echo "WordPress instalado; complemento activo. Importación disponible en Herramientas.\n";
