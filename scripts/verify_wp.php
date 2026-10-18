<?php
/** Comprobaciones de la importación FAC-USO en el WordPress local desechable. */
$_SERVER['HTTP_HOST'] = '127.0.0.1:18086';
$_SERVER['REQUEST_URI'] = '/';
require '/var/www/html/wp-load.php';

if (wp_get_environment_type() !== 'local' || !defined('WP_HTTP_BLOCK_EXTERNAL') || !WP_HTTP_BLOCK_EXTERNAL) {
    throw new RuntimeException('Las pruebas exigen WordPress local con salida HTTP bloqueada.');
}
if (!function_exists('facuso_data')) {
    throw new RuntimeException('El complemento FAC-USO no está activo.');
}

if (in_array('--xmlrpc-qa-count', $argv, true) || in_array('--xmlrpc-qa-cleanup', $argv, true)) {
    $bot = get_user_by('login', 'facuso-bot-granada');
    if (!$bot) {
        throw new RuntimeException('Falta el bot local de Granada.');
    }
    $matches = array_filter(get_posts(['author' => $bot->ID, 'post_type' => 'post',
        'post_status' => ['publish', 'future', 'draft', 'pending', 'private', 'trash'], 'numberposts' => -1]),
        static fn($post) => $post->post_title === 'FACUSO-QA-XMLRPC-DENIED');
    echo 'XMLRPC_QA_POSTS ' . count($matches) . "\n";
    if (in_array('--xmlrpc-qa-cleanup', $argv, true)) {
        foreach ($matches as $post) {
            wp_delete_post($post->ID, true);
        }
    }
    exit(0);
}

if (in_array('--bot-details', $argv, true)) {
    $summary = ['published_by_province' => [], 'bop_by_province' => [], 'cadiz_shared_pdf_notices' => 0,
        'false_ids_present' => [], 'unsafe_title_ids' => [], 'wrong_territory_ids' => []];
    foreach (['almeria', 'cadiz', 'cordoba', 'granada', 'huelva', 'jaen', 'malaga', 'sevilla'] as $province) {
        $user = get_user_by('login', 'facuso-bot-' . $province);
        $items = $user ? get_posts(['author' => $user->ID, 'post_type' => 'post', 'post_status' => 'publish',
            'numberposts' => -1]) : [];
        $summary['published_by_province'][$province] = count($items);
        $summary['bop_by_province'][$province] = 0;
        $cadiz_urls = [];
        $term = get_term_by('slug', $province, 'category');
        foreach ($items as $post) {
            $source = (string) get_post_meta($post->ID, 'facuso_source_url', true);
            $host = strtolower((string) wp_parse_url($source, PHP_URL_HOST));
            if (in_array($host, ['app.dipalme.org', 'www.bopcadiz.es', 'bop.dipucordoba.es', 'bop.dipgra.es',
                's2.diphuelva.es', 'bop.dipujaen.es', 'bopsevilla.dipusevilla.es'], true)) {
                $summary['bop_by_province'][$province]++;
            }
            if ($province === 'cadiz' && $host === 'www.bopcadiz.es') {
                $cadiz_urls[$source] = ($cadiz_urls[$source] ?? 0) + 1;
            }
            $title = $post->post_title;
            if ($title !== wp_strip_all_tags($title) || preg_match('/&(?:#\d+|#x[0-9a-f]+|[a-z]+);/i', $title)) {
                $summary['unsafe_title_ids'][] = $post->ID;
            }
            if (!$term || !in_array((int) $term->term_id, wp_get_post_categories($post->ID), true)) {
                $summary['wrong_territory_ids'][] = $post->ID;
            }
        }
        if ($province === 'cadiz') {
            $summary['cadiz_shared_pdf_notices'] = max($cadiz_urls ?: [0]);
        }
    }
    foreach ([327, 331, 357] as $id) {
        if (get_post($id)) {
            $summary['false_ids_present'][] = $id;
        }
    }
    echo wp_json_encode($summary, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT) . "\n";
    exit(0);
}

foreach ($argv as $argument) {
    if (str_starts_with($argument, '--restore-post=')) {
        $id = absint(substr($argument, strlen('--restore-post=')));
        if (!$id || !get_post_meta($id, '_facuso_key', true) || get_post_status($id) !== 'trash') {
            throw new RuntimeException('La restauración solo admite una noticia propia del paquete en la papelera.');
        }
        wp_untrash_post($id);
        if (get_post_status($id) !== 'publish') {
            throw new RuntimeException('No se pudo restaurar la noticia local.');
        }
        echo "Noticia local restaurada.\n";
        exit(0);
    }
}

if (in_array('--security-fixture', $argv, true) || in_array('--security-cleanup', $argv, true)) {
    require_once ABSPATH . 'wp-admin/includes/user.php';
    $username = 'facuso-qa-subscriber';
    $user = get_user_by('login', $username);
    if (in_array('--security-cleanup', $argv, true)) {
        if ($user) {
            wp_delete_user($user->ID);
        }
        echo "Usuario local de prueba eliminado.\n";
        exit(0);
    }
    if (!$user) {
        $id = wp_create_user($username, 'facuso-local-qa-dummy-only-2026', 'facuso-qa@example.invalid');
        if (is_wp_error($id)) {
            throw new RuntimeException($id->get_error_message());
        }
        $user = get_user_by('id', $id);
    }
    $user->set_role('subscriber');
    wp_set_current_user($user->ID);
    try {
        facuso_import(false);
        throw new RuntimeException('El suscriptor pudo importar.');
    } catch (RuntimeException $error) {
        if ($error->getMessage() !== facuso_text('forbidden')) {
            throw $error;
        }
    }
    echo "Usuario local suscriptor preparado; importación directa denegada.\n";
    exit(0);
}

$data = facuso_data();
$errors = [];
$checks = 0;
$assert = static function (bool $ok, string $message) use (&$errors, &$checks): void {
    $checks++;
    if (!$ok) {
        $errors[] = $message;
    }
};

$admin = get_user_by('login', 'facuso-admin');
$assert($admin instanceof WP_User, 'Falta el administrador local');
if ($admin) {
    wp_set_current_user($admin->ID);
}

$objects = [];
foreach (array_merge($data['pages'], $data['posts']) as $item) {
    $type = $item['type'] ?? 'page';
    $path = $item['path'] ?? $item['slug'];
    $post = get_page_by_path($path, OBJECT, $type);
    $objects[$item['slug']] = $post;
    $assert($post instanceof WP_Post, "Falta {$type}: {$item['slug']}");
    if (!$post) {
        continue;
    }
    $assert($post->post_status === $item['status'], "Estado incorrecto: {$item['slug']}");
    $assert(get_post_meta($post->ID, '_facuso_key', true) === $item['slug'], "Falta autoría del paquete: {$item['slug']}");
    $assert(get_post_meta($post->ID, '_facuso_import_stage', true) === 'complete', "Importación incompleta: {$item['slug']}");
    $assert(!preg_match('/\[\[page:[a-z0-9-]+\]\]/', $post->post_content), "Enlace interno sin resolver: {$item['slug']}");
    $assert(!preg_match('/<\?php|\b(?:Fatal error|Warning:|Notice:)\b/i', $post->post_content), "Contenido de error o PHP: {$item['slug']}");
    if ($type === 'post') {
        $actual = wp_get_post_categories($post->ID, ['fields' => 'slugs']);
        foreach ($item['categories'] ?? [] as $term_slug) {
            $assert(in_array($term_slug, $actual, true), "Categoría ausente {$term_slug}: {$item['slug']}");
        }
        $source = get_post_meta($post->ID, 'facuso_source_url', true);
        if ($source) {
            $assert(str_starts_with($source, 'https://'), "Fuente sin HTTPS: {$item['slug']}");
        }
    }
}
foreach ($data['pages'] as $item) {
    if (empty($item['parent']) || empty($objects[$item['slug']]) || empty($objects[$item['parent']])) {
        continue;
    }
    $assert((int) $objects[$item['slug']]->post_parent === (int) $objects[$item['parent']]->ID,
        "Jerarquía de página incorrecta: {$item['slug']}");
}
foreach ($data['categories'] as $item) {
    $term = get_term_by('slug', $item['slug'], 'category');
    $assert($term instanceof WP_Term, "Falta categoría: {$item['slug']}");
    if ($term && !empty($item['parent'])) {
        $parent = get_term_by('slug', $item['parent'], 'category');
        $assert($parent && (int) $term->parent === (int) $parent->term_id, "Jerarquía de categoría incorrecta: {$item['slug']}");
    }
}
foreach ($data['menus'] as $slug => $entries) {
    $menu = wp_get_nav_menu_object($slug);
    $assert($menu instanceof WP_Term, "Falta menú: {$slug}");
    if (!$menu) {
        continue;
    }
    $items = wp_get_nav_menu_items($menu->term_id) ?: [];
    $by_page = [];
    foreach ($items as $entry) {
        if ($entry->object === 'page') {
            $by_page[(int) $entry->object_id] = $entry;
        }
    }
    foreach ($entries as $entry) {
        $page = $objects[$entry['page']] ?? null;
        if (!$page || $page->post_status !== 'publish') {
            continue;
        }
        $assert(isset($by_page[$page->ID]), "Falta entrada {$entry['page']} en {$slug}");
        if (isset($entry['parent'], $by_page[$page->ID], $objects[$entry['parent']])) {
            $menu_parent = $by_page[$objects[$entry['parent']]->ID] ?? null;
            $assert($menu_parent && (int) $by_page[$page->ID]->menu_item_parent === (int) $menu_parent->ID,
                "Jerarquía del menú incorrecta: {$entry['page']}");
        }
    }
}
$front = (int) get_option('page_on_front');
$assert(get_option('show_on_front') === 'page' && !empty($objects['inicio']) && $front === (int) $objects['inicio']->ID,
    'La portada no es la página Inicio');
$assert(get_stylesheet() === 'facuso-andalucia', 'El tema FAC-USO no está activo');
$images = facuso_images();
$image_ids = get_option('facuso_image_ids', []);
$assert(count($images) === count($image_ids), 'El número de medios importados no coincide con el manifiesto');
foreach ($images as $image) {
    $id = $image_ids[$image['file']] ?? 0;
    $assert($id && get_post_type($id) === 'attachment' && str_starts_with((string) get_post_mime_type($id), 'image/'),
        'Falta medio importado: ' . $image['file']);
}

$provinces = ['almeria', 'cadiz', 'cordoba', 'granada', 'huelva', 'jaen', 'malaga', 'sevilla'];
foreach ($provinces as $slug) {
    $page = $objects[$slug] ?? null;
    $assert($page && preg_match('/mailto:[^"\s<>]+@[^"\s<>]+/', $page->post_content), "Falta correo provincial: {$slug}");
    $phone = $page && preg_match('/Teléfono:\s*([0-9\s.]+)/u', wp_strip_all_tags($page->post_content), $matches)
        ? preg_replace('/\D/', '', $matches[1]) : '';
    $assert(strlen($phone) >= 9, "Falta teléfono provincial: {$slug}");
    $term = get_term_by('slug', $slug, 'category');
    $assert($term instanceof WP_Term, "Falta territorio provincial: {$slug}");
    if ($term) {
        $count = (new WP_Query(['post_type' => 'post', 'post_status' => 'publish', 'posts_per_page' => 1,
            'tax_query' => [['taxonomy' => 'category', 'field' => 'term_id', 'terms' => [$term->term_id]]]]))->found_posts;
        $assert($count > 0, "No hay noticias provinciales: {$slug}");
    }
    if (in_array('--bots', $argv, true)) {
        $bot = get_user_by('login', 'facuso-bot-' . $slug);
        $assert($bot instanceof WP_User, "Falta cuenta del bot: {$slug}");
        if ($bot) {
            $assert(in_array('facuso_news_bot', $bot->roles, true), "Rol del bot incorrecto: {$slug}");
            $assert(get_user_meta($bot->ID, '_facuso_bot_province', true) === $slug, "Ámbito del bot incorrecto: {$slug}");
            $assert(count(WP_Application_Passwords::get_user_application_passwords($bot->ID)) > 0,
                "Falta contraseña de aplicación del bot: {$slug}");
            $bot_news = (new WP_Query(['post_type' => 'post', 'post_status' => 'publish', 'posts_per_page' => 1,
                'author' => $bot->ID]))->found_posts;
            $assert($bot_news > 0, "El bot no publicó noticias: {$slug}");
        }
    }
}
$employment = get_term_by('slug', 'empleo-publico', 'category');
$assert($employment instanceof WP_Term, 'Falta categoría de empleo público');
if ($employment) {
    $count = (new WP_Query(['post_type' => 'post', 'post_status' => 'publish', 'posts_per_page' => 1,
        'cat' => $employment->term_id]))->found_posts;
    $assert($count >= 8, 'Hay menos de ocho publicaciones de empleo público');
}

// Prueba opcional sobre el volumen desechable, ejecutable solo tras terminar la importación.
if (in_array('--mutation', $argv, true) && $admin) {
    $sample = $objects['inicio'] ?? null;
    if ($sample) {
        $old_content = $sample->post_content;
        $old_front = get_option('page_on_front');
        try {
            $marker = '<p>Prueba local de edición</p>';
            wp_update_post(['ID' => $sample->ID, 'post_content' => $old_content . $marker]);
            facuso_import(false);
            $assert(str_ends_with(get_post($sample->ID)->post_content, $marker), 'La reimportación sobrescribió una edición');
            $assert(get_option('page_on_front') === $old_front, 'La reimportación alteró la portada');
            delete_post_meta($sample->ID, '_facuso_import_stage');
            update_post_meta($sample->ID, '_facuso_import_stage', 'pending');
            facuso_import(false);
            $assert(get_post_meta($sample->ID, '_facuso_import_stage', true) === 'complete', 'No se recuperó una importación interrumpida');
            $assert(!str_ends_with(get_post($sample->ID)->post_content, $marker), 'La recuperación no completó el contenido');
        } finally {
            wp_update_post(['ID' => $sample->ID, 'post_content' => $old_content]);
            update_post_meta($sample->ID, '_facuso_import_stage', 'complete');
        }
    }
}

printf("FAC-USO: %d comprobaciones; %d errores; paquete %d páginas, %d noticias, %d categorías.\n",
    $checks, count($errors), count($data['pages']), count($data['posts']), count($data['categories']));
foreach ($errors as $error) {
    fwrite(STDERR, "- {$error}\n");
}
exit($errors ? 1 : 0);
