<?php
/** Ensayo reproducible en el WordPress aislado de docker/compose.validation.yaml. */
declare(strict_types=1);

$mode = $argv[1] ?? '';
if (!in_array($mode, ['zip', 'xml', 'subdir', 'reset-zip', 'reset-xml'], true)) {
    fwrite(STDERR, "Uso: php test_imports.php zip|xml|subdir|reset-zip|reset-xml\n");
    exit(2);
}
if (in_array($mode, ['xml', 'reset-xml'], true) && getenv('WORDPRESS_TABLE_PREFIX') !== 'facuso_wxrtest_') {
    throw new RuntimeException('El XML exige WORDPRESS_TABLE_PREFIX=facuso_wxrtest_.');
}
if (!in_array($mode, ['xml', 'reset-xml'], true) && getenv('WORDPRESS_TABLE_PREFIX') !== 'facuso_ziptest_') {
    throw new RuntimeException('El ZIP exige WORDPRESS_TABLE_PREFIX=facuso_ziptest_.');
}
define('WP_INSTALLING', true);
define('FS_METHOD', 'direct');
$_SERVER['HTTP_HOST'] = '127.0.0.1:18087';
$_SERVER['REQUEST_URI'] = '/';
require '/var/www/html/wp-load.php';
if (wp_get_environment_type() !== 'local' || !defined('WP_HTTP_BLOCK_EXTERNAL') || !WP_HTTP_BLOCK_EXTERNAL) {
    throw new RuntimeException('Solo se admite WordPress local sin salida HTTP externa.');
}
if (str_starts_with($mode, 'reset-')) {
    global $wpdb;
    $prefix = $wpdb->prefix;
    $expected_prefix = $mode === 'reset-xml' ? 'facuso_wxrtest_' : 'facuso_ziptest_';
    if ($prefix !== $expected_prefix) throw new RuntimeException('Prefijo de borrado inesperado.');
    $tables = array_filter($wpdb->get_col('SHOW TABLES'), static fn($table) => str_starts_with($table, $prefix));
    $wpdb->query('SET FOREIGN_KEY_CHECKS=0');
    foreach ($tables as $table) {
        $wpdb->query('DROP TABLE `' . str_replace('`', '``', $table) . '`');
    }
    $wpdb->query('SET FOREIGN_KEY_CHECKS=1');
    echo json_encode(['reset_prefix' => $prefix, 'tables_removed' => count($tables)]) . "\n";
    exit(0);
}
require_once ABSPATH . 'wp-admin/includes/upgrade.php';
require_once ABSPATH . 'wp-admin/includes/plugin.php';
require_once ABSPATH . 'wp-admin/includes/file.php';

$origin = 'http://127.0.0.1:18087';
if (!is_blog_installed()) {
    wp_install('FAC-USO Validación', 'facuso-validation-admin', 'validation@example.invalid', false, '', trim(file_get_contents('/run/secrets/admin_password')), 'es_ES');
    update_option('siteurl', $origin);
    update_option('home', $origin);
    update_option('blog_public', '0');
    // Solo se eliminan los contenidos de muestra del prefijo recién instalado.
    foreach (get_posts(['post_type' => ['page', 'post'], 'post_status' => 'any', 'numberposts' => -1]) as $post) {
        wp_delete_post($post->ID, true);
    }
}
$admin = get_user_by('login', 'facuso-validation-admin');
if (!$admin) {
    throw new RuntimeException('No existe el administrador exclusivo de la validación.');
}
wp_set_current_user($admin->ID);
global $wp_rewrite;
$wp_rewrite->set_permalink_structure('/%postname%/');
$wp_rewrite->flush_rules(true);

$errors = [];
$checks = 0;
$check = static function ($condition, string $message) use (&$errors, &$checks): void {
    $checks++;
    if (!$condition) $errors[] = $message;
};
$install_zip = static function (string $archive): void {
    if (!WP_Filesystem()) throw new RuntimeException('No se pudo activar el sistema de ficheros local.');
    $result = unzip_file($archive, WP_PLUGIN_DIR);
    if (is_wp_error($result)) throw new RuntimeException($result->get_error_message());
};
$count = static function (string $type): int {
    global $wpdb;
    return (int) $wpdb->get_var($wpdb->prepare("SELECT COUNT(*) FROM {$wpdb->posts} WHERE post_type=%s AND post_status NOT IN ('trash','auto-draft')", $type));
};
$data = json_decode(file_get_contents('/importacion/contenido-fuentes.json'), true, 512, JSON_THROW_ON_ERROR);
$expected_pages = count($data['pages']);
$expected_posts = count($data['posts']);
$expected_categories = count($data['categories']);

if ($mode === 'zip') {
    $install_zip('/importacion/facuso-arranque.zip');
    $activated = activate_plugin('facuso-arranque/facuso-arranque.php');
    if (is_wp_error($activated)) throw new RuntimeException($activated->get_error_message());
    if (!function_exists('facuso_import')) throw new RuntimeException('El complemento no cargó la función importadora.');
    $first = facuso_import(true);
    $check($first['created'] === $expected_pages + $expected_posts, 'El primer ZIP no creó todos los contenidos.');
    $check($first['categories'] === $expected_categories, 'El primer ZIP no creó todas las categorías.');
    $check(empty($first['conflicts']), 'El primer ZIP encontró conflictos inesperados.');
    $check(get_stylesheet() === 'facuso-andalucia', 'El diseño del ZIP no se activó.');
    $check(get_option('show_on_front') === 'page', 'El ZIP no configuró la portada.');
    $check($count('page') === $expected_pages, 'Número de páginas ZIP incorrecto.');
    $check($count('post') === $expected_posts, 'Número de noticias ZIP incorrecto.');
    $before = [$count('page'), $count('post'), $count('attachment')];
    $second = facuso_import(true);
    $check($second['created'] === 0 && empty($second['conflicts']), 'Repetir el ZIP creó registros o conflictos.');
    $check($before === [$count('page'), $count('post'), $count('attachment')], 'Repetir el ZIP cambió los conteos.');
    $check(count(wp_get_nav_menu_items('facuso-principal') ?: []) > 0, 'Falta el menú principal.');
    $check(count(wp_get_nav_menu_items('facuso-pie') ?: []) > 0, 'Falta el menú del pie.');
    $check((int) get_option('page_on_front') === get_page_by_path('inicio')->ID, 'Portada incorrecta.');
    $check($count('attachment') === $first['media'], 'El ZIP no creó todos los medios.');
    foreach (get_option('facuso_image_ids', []) as $file => $id) {
        $check(get_post_type($id) === 'attachment' && get_post_mime_type($id) === 'image/webp'
            && is_file(get_attached_file($id)), 'Medio del ZIP ausente o ilegible: ' . $file);
    }
    $result = ['mode' => 'zip', 'first' => $first, 'second' => $second];
} elseif ($mode === 'xml') {
    $install_zip('/pruebas/wordpress-importer.zip');
    define('WP_LOAD_IMPORTERS', true);
    require_once WP_PLUGIN_DIR . '/wordpress-importer/wordpress-importer.php';
    $importer = new WP_Import();
    $importer->fetch_attachments = false;
    ob_start();
    $importer->import('/importacion/facuso-andalucia.xml');
    $import_log = ob_get_clean();
    $check($count('page') === $expected_pages, 'El WXR no creó todas las páginas.');
    $check($count('post') === $expected_posts, 'El WXR no creó todas las noticias.');
    $check(count(wp_get_nav_menu_items('facuso-principal') ?: []) > 0, 'El WXR no creó el menú principal.');
    $check(count(wp_get_nav_menu_items('facuso-pie') ?: []) > 0, 'El WXR no creó el menú del pie.');
    $check(!preg_match('/Failed to import|Error|Fatal error/i', $import_log), 'El importador oficial informó errores.');
    global $wpdb;
    $unresolved = (int) $wpdb->get_var("SELECT COUNT(*) FROM {$wpdb->posts} WHERE post_type IN ('page','post') AND (post_content LIKE '%[[asset:%' OR post_content LIKE '%[facuso_%')");
    $check($unresolved === 0, 'El WXR deja marcadores de imagen dependientes del complemento.');
    $result = ['mode' => 'xml', 'importer' => 'wordpress-importer 0.9.1'];
} else {
    if (!function_exists('facuso_import')) require_once WP_PLUGIN_DIR . '/facuso-arranque/facuso-arranque.php';
    if (!function_exists('facuso_import')) throw new RuntimeException('Importar ZIP antes de ensayar subdirectorio.');
    update_option('siteurl', $origin . '/portal');
    update_option('home', $origin . '/portal');
    $sample = get_page_by_path('conocenos');
    $check($sample instanceof WP_Post, 'Falta la página para probar subdirectorio.');
    if ($sample) $check(str_starts_with(get_permalink($sample), $origin . '/portal/'), 'Enlace de página sin subdirectorio.');
    update_option('siteurl', $origin);
    update_option('home', $origin);
    $result = ['mode' => 'subdir'];
}

$page_paths = array_column($data['pages'], 'path', 'slug');
foreach ($data['pages'] as $item) {
    $page = get_page_by_path($item['path'] ?? $item['slug']);
    $check($page instanceof WP_Post, 'Falta página ' . $item['slug']);
    if (!$page) continue;
    $check($page->post_title === $item['title'], 'Título de página incorrecto ' . $item['slug']);
    if (!empty($item['parent'])) {
        $parent = get_page_by_path($page_paths[$item['parent']] ?? $item['parent']);
        $check($parent && (int) $page->post_parent === (int) $parent->ID, 'Jerarquía incorrecta ' . $item['slug']);
    }
}
foreach ($data['posts'] as $item) {
    $post = get_page_by_path($item['slug'], OBJECT, 'post');
    $check($post instanceof WP_Post, 'Falta noticia ' . $item['slug']);
    if ($post) $check($post->post_title === $item['title'], 'Título de noticia incorrecto ' . $item['slug']);
}
foreach ($data['categories'] as $item) {
    $term = get_term_by('slug', $item['slug'], 'category');
    $check($term instanceof WP_Term, 'Falta categoría ' . $item['slug']);
    if ($term && !empty($item['parent'])) {
        $parent = get_term_by('slug', $item['parent'], 'category');
        $check($parent && (int) $term->parent === (int) $parent->term_id, 'Jerarquía de categoría incorrecta ' . $item['slug']);
    }
}
if ($mode !== 'subdir') {
    global $wpdb;
    $tokens = (int) $wpdb->get_var("SELECT COUNT(*) FROM {$wpdb->posts} WHERE post_type IN ('page','post') AND post_content LIKE '%[[page:%'");
    $check($tokens === 0, 'Quedan enlaces internos sin resolver.');
}
$result += ['checks' => $checks, 'errors' => $errors, 'pages' => $count('page'), 'posts' => $count('post'),
    'attachments' => $count('attachment'), 'expected' => ['pages' => $expected_pages, 'posts' => $expected_posts, 'categories' => $expected_categories],
    'table_prefix' => $GLOBALS['wpdb']->prefix];
if ($errors && isset($import_log)) $result['import_log_excerpt'] = mb_substr(wp_strip_all_tags($import_log), 0, 5000);
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) . "\n";
exit($errors ? 1 : 0);
