<?php
/**
 * Plugin Name: FAC-USO Andalucía · Arranque
 * Description: Importación de contenido documentado, navegación y filtros por sector, materia y provincia.
 * Version: 1.0.0
 * Requires at least: 6.6
 * Requires PHP: 8.1
 * License: GPL-2.0-or-later
 */
defined('ABSPATH') || exit;
require_once __DIR__ . '/includes/external-links.php';

function facuso_register_bot_role(): void {
    add_role('facuso_news_bot', facuso_text('bot_role'), [
        'read' => true, 'edit_posts' => true, 'edit_published_posts' => true, 'publish_posts' => true,
    ]);
}
register_activation_hook(__FILE__, 'facuso_register_bot_role');

add_filter('authenticate', function ($user) {
    if ($user instanceof WP_User && (in_array('facuso_news_bot', (array) $user->roles, true) || get_user_meta($user->ID, '_facuso_bot_province', true))) {
        if (!defined('REST_REQUEST') || !REST_REQUEST) {
            return new WP_Error('facuso_bot_rest_only', facuso_text('bot_rest_only'));
        }
    }
    return $user;
}, 1000);

function facuso_data(): array {
    static $data;
    if ($data === null) {
        $data = json_decode(file_get_contents(__DIR__ . '/content.json'), true, 512, JSON_THROW_ON_ERROR);
    }
    return $data;
}

function facuso_images(): array {
    static $images;
    if ($images === null) {
        $images = json_decode(file_get_contents(__DIR__ . '/images.json'), true, 512, JSON_THROW_ON_ERROR);
    }
    return $images;
}

function facuso_image_for_post(int $post_id): array {
    if (has_post_thumbnail($post_id)) {
        $id = get_post_thumbnail_id($post_id);
        return ['url' => get_the_post_thumbnail_url($post_id, 'large'),
            'alt' => get_post_meta($id, '_wp_attachment_image_alt', true),
            'credit' => get_post_field('post_excerpt', $id), 'kind' => get_post_meta($id, '_facuso_image_kind', true)];
    }
    $images = facuso_images();
    $source = get_post_meta($post_id, 'facuso_source_url', true);
    foreach ($images as $image) {
        if (!empty($image['source_url']) && $image['source_url'] === $source && $image['kind'] === 'original') {
            return array_merge($image, ['url' => plugins_url('theme/assets/' . $image['file'], __FILE__)]);
        }
    }
    $slugs = wp_get_post_categories($post_id, ['fields' => 'slugs']);
    $slug = get_post_field('post_name', $post_id);
    $key = in_array('formacion', $slugs, true) || $slug === 'formacion' ? 'formacion' :
        (in_array('sanidad', $slugs, true) || in_array('salud-laboral', $slugs, true) || in_array($slug, ['sanidad', 'salud-laboral'], true) ? 'sanidad' :
        (in_array('administracion-de-justicia', $slugs, true) || in_array($slug, ['administracion-de-justicia', 'asesoria-juridica'], true) ? 'justicia' : 'empleo'));
    if ($key === 'empleo') {
        $pool = array_values(array_filter($images, fn($image) => $image['kind'] === 'generated' && str_starts_with($image['file'], 'foto-empleo')));
        if ($pool) {
            $image = $pool[(int) sprintf('%u', crc32($slug)) % count($pool)];
            return array_merge($image, ['url' => plugins_url('theme/assets/' . $image['file'], __FILE__)]);
        }
    }
    foreach ($images as $image) {
        if ($image['file'] === 'foto-' . $key . '.webp') {
            return array_merge($image, ['url' => plugins_url('theme/assets/' . $image['file'], __FILE__)]);
        }
    }
    return [];
}

function facuso_import_media(): array {
    require_once ABSPATH . 'wp-admin/includes/image.php';
    require_once ABSPATH . 'wp-admin/includes/file.php';
    $ids = get_option('facuso_image_ids', []);
    foreach (facuso_images() as $image) {
        $key = $image['file'];
        if (isset($ids[$key]) && get_post_type($ids[$key]) === 'attachment') {
            continue;
        }
        // Catálogo fijo incluido en el paquete; nunca se descargan URL del visitante.
        $path = realpath(__DIR__ . '/theme/assets/' . $key);
        $root = realpath(__DIR__ . '/theme/assets') . DIRECTORY_SEPARATOR;
        if (!$path || !str_starts_with($path, $root) || !str_ends_with($path, '.webp') || filesize($path) > 6000000) {
            throw new RuntimeException(facuso_text('media_error'));
        }
        $upload = wp_upload_bits(basename($key), null, file_get_contents($path));
        if ($upload['error']) {
            throw new RuntimeException(facuso_text('media_error'));
        }
        $id = facuso_checked(wp_insert_attachment([
            'post_mime_type' => 'image/webp', 'post_title' => $image['alt'],
            'post_excerpt' => $image['credit'], 'post_content' => $image['description'] ?? '',
            'post_status' => 'inherit',
        ], $upload['file'], 0, true));
        update_post_meta($id, '_wp_attachment_image_alt', $image['alt']);
        update_post_meta($id, '_facuso_image_kind', $image['kind']);
        update_post_meta($id, '_facuso_image_file', $key);
        $metadata = wp_generate_attachment_metadata($id, $upload['file']);
        wp_update_attachment_metadata($id, $metadata);
        $ids[$key] = $id;
        update_option('facuso_image_ids', $ids, false);
    }
    return $ids;
}

function facuso_text(string $key): string {
    static $texts;
    if ($texts === null) {
        $texts = json_decode(file_get_contents(__DIR__ . '/languages/es.json'), true, 512, JSON_THROW_ON_ERROR);
    }
    return $texts[$key] ?? $key;
}

add_action('admin_menu', function () {
    add_management_page(facuso_text('installer'), facuso_text('installer'), 'manage_options', 'facuso-arranque', 'facuso_admin');
});

function facuso_admin(): void {
    if (!current_user_can('manage_options')) {
        return;
    }
    $data = facuso_data();
    echo '<div class="wrap"><h1>' . esc_html(facuso_text('installer')) . '</h1>';
    echo '<p>' . esc_html(facuso_text('intro_install')) . '</p>';
    echo '<p>' . esc_html(sprintf(facuso_text('counts'), count($data['pages']), count($data['posts']), count($data['categories']))) . '</p>';
    if (isset($_GET['facuso_done'])) {
        echo '<div class="notice notice-success"><p>' . esc_html(facuso_text('import_done')) . '</p></div>';
    }
    $report = get_option('facuso_last_import', []);
    if ($report) {
        echo '<pre>' . esc_html(wp_json_encode($report, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE)) . '</pre>';
    }
    echo '<form method="post" action="' . esc_url(admin_url('admin-post.php')) . '">';
    wp_nonce_field('facuso_import');
    echo '<input type="hidden" name="action" value="facuso_import">';
    echo '<p><label><input type="checkbox" name="design" value="1" checked> ' . esc_html(facuso_text('install_design')) . '</label></p>';
    echo '<p>' . esc_html(facuso_text('no_overwrite')) . '</p>';
    submit_button(facuso_text('import_button'));
    echo '</form><h2>' . esc_html(facuso_text('pending')) . '</h2><ul>';
    foreach ($data['pending'] as $note) {
        echo '<li>' . esc_html($note) . '</li>';
    }
    echo '</ul></div>';
}

add_action('admin_post_facuso_import', function () {
    if (!current_user_can('manage_options') || !current_user_can('publish_pages') || !current_user_can('publish_posts')) {
        wp_die(esc_html(facuso_text('forbidden')), '', ['response' => 403]);
    }
    check_admin_referer('facuso_import');
    $design = isset($_POST['design']) && $_POST['design'] === '1';
    if ($design && (!current_user_can('install_themes') || !current_user_can('switch_themes'))) {
        wp_die(esc_html(facuso_text('forbidden')), '', ['response' => 403]);
    }
    try {
        facuso_import($design);
    } catch (Throwable $error) {
        wp_die(esc_html($error->getMessage()), '', ['response' => 500]);
    }
    wp_safe_redirect(admin_url('tools.php?page=facuso-arranque&facuso_done=1'));
    exit;
});

function facuso_checked($result) {
    if (is_wp_error($result)) {
        throw new RuntimeException($result->get_error_message());
    }
    return $result;
}

function facuso_install_design(): void {
    require_once ABSPATH . 'wp-admin/includes/file.php';
    // Todos los ficheros proceden del paquete. No se admiten rutas ni URL del formulario.
    $destination = get_theme_root() . '/facuso-andalucia';
    if (!is_dir($destination)) {
        if (!WP_Filesystem()) {
            throw new RuntimeException(facuso_text('filesystem_error'));
        }
        global $wp_filesystem;
        $staging = get_theme_root() . '/.facuso-' . wp_generate_uuid4();
        if (!$wp_filesystem->mkdir($staging)) {
            throw new RuntimeException(facuso_text('filesystem_error'));
        }
        try {
            facuso_checked(copy_dir(__DIR__ . '/theme', $staging));
            foreach (['style.css', 'index.php', 'header.php', 'footer.php', 'functions.php', 'facuso-theme.marker'] as $required) {
                if (!$wp_filesystem->is_file($staging . '/' . $required)) {
                    throw new RuntimeException(facuso_text('filesystem_error'));
                }
            }
            if (!$wp_filesystem->move($staging, $destination, false)) {
                throw new RuntimeException(facuso_text('filesystem_error'));
            }
        } finally {
            if ($wp_filesystem->is_dir($staging)) {
                $wp_filesystem->delete($staging, true);
            }
        }
        wp_clean_themes_cache();
    } elseif (!is_file($destination . '/facuso-theme.marker')) {
        throw new RuntimeException(facuso_text('theme_conflict'));
    }
    foreach (['style.css', 'index.php', 'functions.php', 'header.php', 'footer.php'] as $required) {
        if (!is_file($destination . '/' . $required)) {
            throw new RuntimeException(facuso_text('filesystem_error'));
        }
    }
    switch_theme('facuso-andalucia');
}

function facuso_import(bool $design = false): array {
    if (!current_user_can('manage_options') || !current_user_can('publish_pages') || !current_user_can('publish_posts')) {
        throw new RuntimeException(facuso_text('forbidden'));
    }
    if ($design && (!current_user_can('install_themes') || !current_user_can('switch_themes'))) {
        throw new RuntimeException(facuso_text('forbidden'));
    }
    // add_option usa una clave única; evita dos importaciones simultáneas.
    $lock = (int) get_option('facuso_import_lock', 0);
    if ($lock && $lock < time() - 600) {
        delete_option('facuso_import_lock');
    }
    if (!add_option('facuso_import_lock', time(), '', false)) {
        throw new RuntimeException(facuso_text('locked'));
    }
    try {
        $data = facuso_data();
        $report = ['created' => 0, 'recovered' => 0, 'adopted' => 0, 'skipped' => 0, 'categories' => 0, 'menus' => 0, 'conflicts' => []];
        $terms = [];
        foreach ($data['categories'] as $category) {
            $term = get_term_by('slug', $category['slug'], 'category');
            if (!$term) {
                $new = facuso_checked(wp_insert_term($category['title'], 'category', [
                    'slug' => $category['slug'], 'parent' => $terms[$category['parent']] ?? 0,
                    'description' => $category['description'] ?? '',
                ]));
                $terms[$category['slug']] = (int) $new['term_id'];
                $report['categories']++;
            } else {
                $terms[$category['slug']] = (int) $term->term_id;
            }
        }
        $ids = [];
        $inserted = [];
        foreach (array_merge($data['pages'], $data['posts']) as $item) {
            $type = $item['type'] ?? 'page';
            $path = $item['path'] ?? $item['slug'];
            $existing = get_page_by_path($path, OBJECT, $type);
            if (!$existing) {
                $same_slug = get_posts(['name' => $item['slug'], 'post_type' => $type,
                    'post_status' => ['publish', 'draft', 'pending', 'private', 'future'], 'numberposts' => 1]);
                $existing = $same_slug[0] ?? null;
            }
            if ($existing) {
                $ids[$item['slug']] = (int) $existing->ID;
                $external = get_post_meta($existing->ID, 'facuso_external_id', true);
                $source = get_post_meta($existing->ID, 'facuso_source_url', true);
                if (!get_post_meta($existing->ID, '_facuso_key', true) && !empty($item['external_id']) && is_string($external) && is_string($source)
                    && hash_equals($item['external_id'], $external) && hash_equals($item['sources'][0]['url'] ?? '', $source)) {
                    // Una noticia propia de los bots ya presente en la captura se
                    // reconoce por ambas claves, sin reemplazar su texto ni estado.
                    update_post_meta($existing->ID, '_facuso_key', $item['slug']);
                    update_post_meta($existing->ID, '_facuso_import_stage', 'complete');
                    update_post_meta($existing->ID, '_facuso_sources', $item['sources'] ?? []);
                    $report['adopted']++;
                }
                if (get_post_meta($existing->ID, '_facuso_key', true) === $item['slug'] && get_post_meta($existing->ID, '_facuso_import_stage', true) === 'pending') {
                    $inserted[$item['slug']] = $item;
                    $report['recovered']++;
                    continue;
                }
                $report['skipped']++;
                if (!get_post_meta($existing->ID, '_facuso_key', true)) {
                    $report['conflicts'][] = $item['slug'];
                }
                continue;
            }
            $id = facuso_checked(wp_insert_post([
                'post_type' => $type, 'post_title' => $item['title'], 'post_name' => $item['slug'],
                'post_status' => $item['status'], 'post_content' => wp_kses_post($item['html']),
                'post_excerpt' => $item['excerpt'] ?? '', 'post_date' => $item['date'] ?? current_time('mysql'),
                'post_parent' => $ids[$item['parent'] ?? ''] ?? 0,
                'post_author' => get_current_user_id(), 'comment_status' => 'closed', 'ping_status' => 'closed',
                'meta_input' => ['_facuso_key' => $item['slug'], '_facuso_import_stage' => 'pending'],
            ], true));
            if (!$id) {
                throw new RuntimeException(facuso_text('post_error'));
            }
            $ids[$item['slug']] = $id;
            $inserted[$item['slug']] = $item;
            update_post_meta($id, '_facuso_key', $item['slug']);
            $report['created']++;
        }
        // Resuelve las referencias internas contra los ID reales, incluso con WordPress en subdirectorio.
        foreach ($inserted as $slug => $item) {
            update_post_meta($ids[$slug], '_facuso_sources', $item['sources'] ?? []);
            update_post_meta($ids[$slug], '_facuso_review', $item['notes'] ?? []);
            if (!empty($item['sources'][0]['url'])) {
                update_post_meta($ids[$slug], 'facuso_source_url', esc_url_raw($item['sources'][0]['url'], ['https']));
            }
            if (!empty($item['external_id'])) {
                update_post_meta($ids[$slug], 'facuso_external_id', sanitize_text_field($item['external_id']));
            }
            if (($item['type'] ?? 'page') === 'post' && !empty($item['categories'])) {
                facuso_checked(wp_set_post_categories($ids[$slug], array_values(array_filter(array_map(
                    fn($term_slug) => $terms[$term_slug] ?? null, $item['categories']
                )))));
            }
            $content = preg_replace_callback('/\[\[page:([a-z0-9-]+)\]\]/', function ($match) use ($ids) {
                return isset($ids[$match[1]]) ? esc_url(get_permalink($ids[$match[1]])) : '#';
            }, $item['html']);
            $content = preg_replace_callback('/\[\[asset:([a-z0-9.\/-]+)\]\]/', function ($match) {
                return esc_url(plugins_url('theme/assets/' . $match[1], __FILE__));
            }, $content);
            facuso_checked(wp_update_post(['ID' => $ids[$slug], 'post_content' => wp_kses_post($content)], true));
            update_post_meta($ids[$slug], '_facuso_import_stage', 'complete');
        }
        $report['media'] = count(facuso_import_media());
        foreach ($data['menus'] as $menu_slug => $menu_data) {
            $menu = wp_get_nav_menu_object($menu_slug);
            if ($menu && !get_term_meta($menu->term_id, '_facuso_managed', true)) {
                continue;
            }
            $menu_id = $menu ? (int) $menu->term_id : facuso_checked(wp_create_nav_menu($menu_slug));
            update_term_meta($menu_id, '_facuso_managed', true);
            $menu_ids = [];
            foreach (wp_get_nav_menu_items($menu_id) ?: [] as $existing_item) {
                if ($existing_item->object === 'page') {
                    $menu_ids[(int) $existing_item->object_id] = (int) $existing_item->ID;
                }
            }
            foreach ($menu_data as $entry) {
                if (!isset($ids[$entry['page']]) || get_post_status($ids[$entry['page']]) !== 'publish') {
                    continue;
                }
                if (isset($menu_ids[$ids[$entry['page']]])) {
                    continue;
                }
                $parent_page_id = $ids[$entry['parent'] ?? ''] ?? 0;
                $menu_ids[$ids[$entry['page']]] = facuso_checked(wp_update_nav_menu_item($menu_id, 0, [
                    'menu-item-object-id' => $ids[$entry['page']], 'menu-item-object' => 'page',
                    'menu-item-type' => 'post_type', 'menu-item-status' => 'publish',
                    'menu-item-title' => $entry['title'] ?? get_the_title($ids[$entry['page']]),
                    'menu-item-parent-id' => $menu_ids[$parent_page_id] ?? 0,
                ]));
            }
            $report['menus']++;
        }
        if ($design) {
            facuso_install_design();
            $locations = get_theme_mod('nav_menu_locations', []);
            foreach (['primary' => 'facuso-principal', 'footer' => 'facuso-pie'] as $location => $menu_slug) {
                $menu = wp_get_nav_menu_object($menu_slug);
                if ($menu) {
                    $locations[$location] = (int) $menu->term_id;
                }
            }
            set_theme_mod('nav_menu_locations', $locations);
        }
        // Solo configura la portada cuando fue creada por este paquete.
        if ($design && !get_option('facuso_home_configured') && isset($ids['inicio']) && get_post_meta($ids['inicio'], '_facuso_key', true) === 'inicio') {
            update_option('facuso_previous_home', ['show_on_front' => get_option('show_on_front'), 'page_on_front' => get_option('page_on_front')]);
            update_option('show_on_front', 'page');
            update_option('page_on_front', $ids['inicio']);
            update_option('facuso_home_configured', true);
        }
        if ($design && !get_option('facuso_site_configured')) {
            update_option('facuso_previous_settings', ['blogname' => get_option('blogname'), 'blogdescription' => get_option('blogdescription')]);
            update_option('blogname', $data['site']['title']);
            update_option('blogdescription', $data['site']['description']);
            update_option('facuso_site_configured', true);
        }
        update_option('facuso_imported', $data['version']);
        update_option('facuso_last_import', $report, false);
        return $report;
    } finally {
        delete_option('facuso_import_lock');
    }
}

add_shortcode('facuso_secciones', function () {
    if (!is_singular('page')) {
        return '';
    }
    $children = get_pages(['parent' => get_the_ID(), 'sort_column' => 'menu_order,post_title', 'post_status' => 'publish']);
    if (!$children) {
        return '';
    }
    $html = '<nav class="fac-sections" aria-label="' . esc_attr(facuso_text('subsections')) . '"><ul>';
    foreach ($children as $child) {
        $html .= '<li><a href="' . esc_url(get_permalink($child)) . '">' . esc_html($child->post_title) . '</a></li>';
    }
    return $html . '</ul></nav>';
});

function facuso_dimension(string $slug, string $root): ?WP_Term {
    $term = get_term_by('slug', $slug, 'category');
    $parent = get_term_by('slug', $root, 'category');
    if (!$term || !$parent || !in_array((int) $parent->term_id, array_map('intval', get_ancestors($term->term_id, 'category')), true)) {
        return null;
    }
    return $term;
}

function facuso_employment_sources(): array {
    static $sources;
    if ($sources === null) {
        $sources = json_decode(file_get_contents(__DIR__ . '/employment-sources.json'), true, 512, JSON_THROW_ON_ERROR);
    }
    return $sources;
}

function facuso_source_pattern(string $kind, string $province = ''): string {
    if (!in_array($kind, ['bop', 'boe'], true)) {
        return '';
    }
    $hosts = [];
    $provinces = array_column(array_filter(facuso_employment_sources(), fn($source) => $source['kind'] === 'bop'), 'province');
    $province = in_array($province, $provinces, true) ? $province : '';
    foreach (facuso_employment_sources() as $source) {
        if ($source['kind'] !== $kind || ($kind === 'bop' && $province !== '' && $source['province'] !== $province)) {
            continue;
        }
        foreach ($source['hosts'] as $host) {
            if (preg_match('/^[a-z0-9.-]+$/D', $host)) {
                $hosts[] = str_replace('.', '[.]', $host);
            }
        }
    }
    return $hosts ? '^https://(' . implode('|', $hosts) . ')(/|$)' : '^https://invalid[.]example[.]invalid/$';
}

function facuso_post_source_label(int $post_id): string {
    $host = strtolower((string) wp_parse_url(get_post_meta($post_id, 'facuso_source_url', true), PHP_URL_HOST));
    foreach (facuso_employment_sources() as $source) {
        if (in_array($host, $source['hosts'], true)) {
            return $source['label'];
        }
    }
    return '';
}

add_shortcode('facuso_publicaciones', function ($atts) {
    $atts = shortcode_atts(['sector' => '', 'materia' => '', 'territorio' => '', 'fuente' => '', 'titulo' => '', 'limite' => '9', 'excluir_empleo' => '0', 'filtros' => '1'], $atts);
    $query = ['post_type' => 'post', 'post_status' => 'publish', 'posts_per_page' => min(18, max(3, absint($atts['limite']))),
        'orderby' => ['date' => 'DESC', 'ID' => 'DESC'],
        'paged' => $atts['filtros'] === '0' ? 1 : min(500, max(1, absint($_GET['fac_pagina'] ?? 1)))];
    $show_source = $atts['fuente'] !== '' || $atts['materia'] === 'empleo-publico';
    $selected_source = in_array($atts['fuente'], ['bop', 'boe'], true) ? $atts['fuente'] : '';
    if ($show_source && $atts['filtros'] !== '0' && isset($_GET['fac_fuente']) && is_string($_GET['fac_fuente'])) {
        $requested_source = wp_unslash($_GET['fac_fuente']);
        if (in_array($requested_source, ['', 'bop', 'boe'], true)) {
            $selected_source = $requested_source;
        }
    }
    if ($selected_source !== '') {
        $source_province = $atts['territorio'];
        if (!$source_province && isset($_GET['fac_territorio']) && is_string($_GET['fac_territorio'])) {
            $source_province = sanitize_title(wp_unslash($_GET['fac_territorio']));
        }
        $query['meta_query'] = [[
            'key' => 'facuso_source_url', 'value' => facuso_source_pattern($selected_source, $source_province), 'compare' => 'REGEXP',
        ]];
    }
    $tax = ['relation' => 'AND'];
    if ($atts['excluir_empleo'] === '1') {
        $employment = get_term_by('slug', 'empleo-publico', 'category');
        if ($employment) {
            $tax[] = ['taxonomy' => 'category', 'field' => 'term_id', 'terms' => [(int) $employment->term_id], 'operator' => 'NOT IN', 'include_children' => true];
        }
    }
    $html = '<section class="fac-news"><h2>' . esc_html($atts['titulo'] ?: facuso_text('news')) . '</h2><form class="fac-filters" method="get" action="' . esc_url(get_permalink()) . '">';
    // Compatible con instalaciones sin enlaces permanentes.
    if (!get_option('permalink_structure')) {
        $html .= '<input type="hidden" name="page_id" value="' . absint(get_the_ID()) . '">';
    }
    foreach (['sector' => 'sectores', 'materia' => 'materias', 'territorio' => 'territorios'] as $dimension => $root) {
        $value = $atts[$dimension];
        if (!$value && isset($_GET['fac_' . $dimension]) && is_string($_GET['fac_' . $dimension])) {
            $value = sanitize_title(wp_unslash($_GET['fac_' . $dimension]));
        }
        $selected = $value ? facuso_dimension($value, $root) : null;
        if ($selected) {
            $tax[] = ['taxonomy' => 'category', 'field' => 'term_id', 'terms' => [(int) $selected->term_id], 'include_children' => true];
        }
        $id = 'fac-' . $dimension;
        $html .= '<label for="' . esc_attr($id) . '">' . esc_html(facuso_text($dimension)) . '<select id="' . esc_attr($id) . '" name="fac_' . esc_attr($dimension) . '">';
        $html .= '<option value="">' . esc_html(facuso_text('all')) . '</option>';
        $parent = get_term_by('slug', $root, 'category');
        $terms = $parent ? get_terms(['taxonomy' => 'category', 'child_of' => $parent->term_id, 'hide_empty' => false, 'orderby' => 'name']) : [];
        if (!is_wp_error($terms)) {
            foreach ($terms as $term) {
                if ($atts['excluir_empleo'] === '1' && $dimension === 'materia' && ($term->slug === 'empleo-publico' || facuso_dimension($term->slug, 'empleo-publico'))) {
                    continue;
                }
                if ($atts[$dimension] && $term->slug !== $atts[$dimension]) {
                    continue;
                }
                $html .= '<option value="' . esc_attr($term->slug) . '"' . selected($selected ? $selected->slug : '', $term->slug, false) . '>' . esc_html($term->name) . '</option>';
            }
        }
        $html .= '</select></label>';
    }
    if ($show_source) {
        $html .= '<label for="fac-fuente">' . esc_html(facuso_text('source')) . '<select id="fac-fuente" name="fac_fuente">';
        foreach (['bop' => 'source_bop', 'boe' => 'source_boe', '' => 'source_all'] as $value => $label) {
            $html .= '<option value="' . esc_attr($value) . '"' . selected($selected_source, $value, false) . '>' . esc_html(facuso_text($label)) . '</option>';
        }
        $html .= '</select></label>';
    }
    $html .= '<button type="submit">' . esc_html(facuso_text('filter')) . '</button><a href="' . esc_url(get_permalink()) . '">' . esc_html(facuso_text('reset')) . '</a></form>';
    if ($atts['filtros'] === '0') {
        $html = '<section class="fac-news"><h2>' . esc_html($atts['titulo'] ?: facuso_text('news')) . '</h2>';
    }
    if (count($tax) > 1) {
        $query['tax_query'] = $tax;
    }
    $posts = new WP_Query($query);
    $html .= '<p class="fac-count">' . esc_html(sprintf(facuso_text('results'), (int) $posts->found_posts)) . '</p><div class="fac-grid">';
    foreach ($posts->posts as $post) {
        $photo = facuso_image_for_post((int) $post->ID);
        $html .= '<article class="fac-card">';
        if ($photo) {
            $html .= '<a class="fac-card-photo" tabindex="-1" aria-hidden="true" href="' . esc_url(get_permalink($post)) . '"><img loading="lazy" decoding="async" width="1280" height="720" src="' . esc_url($photo['url']) . '" alt=""><span>' . esc_html($photo['kind'] === 'original' ? $photo['credit'] : facuso_text('illustrative_photo')) . '</span></a>';
        }
        $label = facuso_post_source_label((int) $post->ID);
        $html .= '<div class="fac-card-body"><p class="fac-meta">' . esc_html(get_the_date('', $post)) . ($label ? ' · ' . esc_html($label) : '') . '</p><h3><a href="' . esc_url(get_permalink($post)) . '">' . esc_html($post->post_title) . '</a></h3><p>' . esc_html(wp_trim_words(wp_strip_all_tags($post->post_content), 38)) . '</p></div></article>';
    }
    if (!$posts->found_posts) {
        $html .= '<p>' . esc_html(facuso_text($selected_source === 'bop' ? 'no_bop_results' : 'no_results')) . '</p>';
    }
    $html .= '</div>';
    if ($posts->max_num_pages > 1 && $atts['filtros'] !== '0') {
        $html .= '<nav class="fac-pagination" aria-label="' . esc_attr(facuso_text('pagination')) . '">';
        $current = min((int) $posts->max_num_pages, (int) $query['paged']);
        foreach (range(max(1, $current - 2), min((int) $posts->max_num_pages, $current + 2)) as $number) {
            $html .= '<a' . ($number === $current ? ' aria-current="page"' : '') . ' href="' . esc_url(add_query_arg('fac_pagina', $number)) . '">' . absint($number) . '</a> ';
        }
        $html .= '</nav>';
    }
    return $html . '</section>';
});

add_shortcode('facuso_imagen', function ($atts) {
    $atts = shortcode_atts(['file' => 'foto-empleo.webp'], $atts);
    foreach (facuso_images() as $photo) {
        if ($photo['file'] === $atts['file']) {
            return '<figure class="fac-section-photo"><img loading="lazy" decoding="async" width="1280" height="720" src="' . esc_url(plugins_url('theme/assets/' . $photo['file'], __FILE__)) . '" alt="' . esc_attr($photo['alt']) . '"><figcaption>' . esc_html($photo['credit']) . '</figcaption></figure>';
        }
    }
    return '';
});

add_shortcode('facuso_galeria', function () {
    $html = '<div class="fac-grid fac-photo-gallery">';
    foreach (facuso_images() as $photo) {
        if ($photo['kind'] !== 'original') {
            continue;
        }
        $html .= '<figure><a href="' . esc_url($photo['source_url']) . '"><img width="1280" height="720" loading="lazy" src="' . esc_url(plugins_url('theme/assets/' . $photo['file'], __FILE__)) . '" alt="' . esc_attr($photo['alt']) . '"></a><figcaption>' . esc_html($photo['credit']) . '</figcaption></figure>';
    }
    return $html . '</div>';
});

// El bot reutiliza la API autenticada de WordPress; no existe un endpoint anónimo propio.
add_action('init', function () {
    register_post_meta('post', 'facuso_source_url', [
        'type' => 'string', 'single' => true, 'show_in_rest' => true,
        'sanitize_callback' => fn($value) => esc_url_raw($value, ['https']),
        'auth_callback' => fn($allowed, $key, $post_id) => current_user_can('edit_post', $post_id),
    ]);
    register_post_meta('post', 'facuso_external_id', [
        'type' => 'string', 'single' => true, 'show_in_rest' => true,
        'sanitize_callback' => 'sanitize_text_field',
        'auth_callback' => fn($allowed, $key, $post_id) => current_user_can('edit_post', $post_id),
    ]);
});

// Las contraseñas de aplicación de los bots están limitadas a publicar noticias
// propias y a su provincia. El servidor no acepta del cliente otra identidad.
add_filter('rest_pre_insert_post', function ($prepared, $request) {
    $user = wp_get_current_user();
    $province = get_user_meta($user->ID, '_facuso_bot_province', true);
    if (!$province && !in_array('facuso_news_bot', (array) $user->roles, true)) {
        return $prepared;
    }
    if (!in_array($province, ['almeria', 'cadiz', 'cordoba', 'granada', 'huelva', 'jaen', 'malaga', 'sevilla'], true)) {
        return new WP_Error('facuso_bot_province', facuso_text('bot_scope_error'), ['status' => 403]);
    }
    $categories = $request->get_param('categories');
    if ($categories === null && $request->get_param('id')) {
        $categories = wp_get_post_categories((int) $request->get_param('id'));
    }
    $has_province = false;
    foreach ((array) $categories as $term_id) {
        $term = get_term((int) $term_id, 'category');
        if (!$term || is_wp_error($term)) {
            return new WP_Error('facuso_bot_category', facuso_text('bot_scope_error'), ['status' => 403]);
        }
        if ($term->slug === $province) {
            $has_province = true;
        } elseif (facuso_dimension($term->slug, 'territorios') || $term->slug === 'territorios') {
            return new WP_Error('facuso_bot_scope', facuso_text('bot_scope_error'), ['status' => 403]);
        }
    }
    if (!$has_province) {
        return new WP_Error('facuso_bot_scope', facuso_text('bot_scope_error'), ['status' => 403]);
    }
    $meta = $request->get_param('meta');
    $source = $meta['facuso_source_url'] ?? ($request->get_param('id') ? get_post_meta((int) $request->get_param('id'), 'facuso_source_url', true) : '');
    $host = strtolower((string) wp_parse_url($source, PHP_URL_HOST));
    $allowed = json_decode(file_get_contents(__DIR__ . '/allowed-source-hosts.json'), true);
    if (wp_parse_url($source, PHP_URL_SCHEME) !== 'https' || !in_array($host, $allowed, true) || wp_parse_url($source, PHP_URL_USER) || wp_parse_url($source, PHP_URL_PASS)) {
        return new WP_Error('facuso_bot_source', facuso_text('bot_source_error'), ['status' => 403]);
    }
    return $prepared;
}, 10, 2);

require_once __DIR__ . '/muestra-tcae.php';
