<?php
defined('ABSPATH') || exit;

function fac_theme_text(string $key): string {
    static $texts;
    if ($texts === null) {
        $texts = json_decode(file_get_contents(__DIR__ . '/languages/es.json'), true, 512, JSON_THROW_ON_ERROR);
    }
    return $texts[$key] ?? $key;
}

add_action('after_setup_theme', function () {
    add_theme_support('title-tag');
    add_theme_support('post-thumbnails');
    add_theme_support('html5', ['search-form', 'gallery', 'caption', 'style', 'script']);
    add_theme_support('responsive-embeds');
    add_theme_support('editor-styles');
    add_editor_style('style.css');
    register_nav_menus([
        'primary' => fac_theme_text('navigation'),
        'footer' => fac_theme_text('footer_navigation'),
    ]);
});

add_action('wp_enqueue_scripts', function () {
    wp_enqueue_style('facuso-theme', get_stylesheet_uri(), [], '1.0.0');
    wp_enqueue_script('facuso-theme', get_template_directory_uri() . '/assets/navigation.js', [], '1.0.0', true);
});

function fac_theme_page(string $slug): string {
    $page = get_posts(['post_type' => 'page', 'name' => $slug, 'post_status' => 'publish', 'numberposts' => 1]);
    return $page ? get_permalink($page[0]) : home_url('/');
}

function fac_theme_context(): array {
    $provinces = ['almeria', 'cadiz', 'cordoba', 'granada', 'huelva', 'jaen', 'malaga', 'sevilla'];
    $sectors = ['administracion-de-justicia', 'sanidad', 'administracion-local', 'administracion-autonomica', 'administracion-general-del-estado'];
    $slugs = [];
    if (is_singular('page')) {
        $slugs[] = get_post_field('post_name', get_queried_object_id());
        foreach (get_post_ancestors(get_queried_object_id()) as $ancestor) {
            $slugs[] = get_post_field('post_name', $ancestor);
        }
    } elseif (is_singular('post')) {
        $slugs = wp_get_post_categories(get_queried_object_id(), ['fields' => 'slugs']);
    } elseif (is_category()) {
        $slugs[] = get_queried_object()->slug;
    }
    foreach ($slugs as $slug) {
        if (in_array($slug, $provinces, true)) {
            return ['title' => fac_theme_text($slug), 'image' => get_template_directory_uri() . '/assets/' . $slug . '.png', 'kind' => 'province'];
        }
    }
    foreach ($slugs as $slug) {
        if (in_array($slug, $sectors, true)) {
            $image = get_theme_mod('fac_logo_' . $slug, '');
            if (!$image && $slug === 'administracion-de-justicia') {
                $image = get_template_directory_uri() . '/assets/justicia.jpg';
            }
            return ['title' => fac_theme_text($slug), 'image' => $image, 'kind' => 'sector'];
        }
    }
    return [];
}

add_action('customize_register', function ($customizer) {
    $customizer->add_section('facuso_logos', ['title' => fac_theme_text('sector_logos'), 'priority' => 35]);
    foreach (['administracion-de-justicia', 'sanidad', 'administracion-local', 'administracion-autonomica', 'administracion-general-del-estado'] as $slug) {
        $key = 'fac_logo_' . $slug;
        $customizer->add_setting($key, ['default' => '', 'sanitize_callback' => 'esc_url_raw']);
        $customizer->add_control(new WP_Customize_Image_Control($customizer, $key, [
            'label' => fac_theme_text($slug), 'section' => 'facuso_logos',
        ]));
    }
});

class Facuso_Menu_Walker extends Walker_Nav_Menu {
    public function start_el(&$output, $item, $depth = 0, $args = null, $id = 0) {
        parent::start_el($output, $item, $depth, $args, $id);
        if (in_array('menu-item-has-children', $item->classes, true)) {
            $output .= '<button class="fac-sub-toggle" type="button" aria-expanded="false" aria-label="' . esc_attr(sprintf(fac_theme_text('open_submenu'), $item->title)) . '"><span aria-hidden="true">⌄</span></button>';
        }
    }
}

function fac_theme_sources(): void {
    $sources = get_post_meta(get_the_ID(), '_facuso_sources', true);
    $single = get_post_meta(get_the_ID(), 'facuso_source_url', true);
    if (!$sources && $single) {
        $sources = [['url' => $single, 'title' => fac_theme_text('original_source')]];
    }
    if (!$sources || !is_array($sources)) {
        return;
    }
    echo '<details class="fac-sources"><summary>' . esc_html(fac_theme_text('sources')) . '</summary><ul>';
    foreach ($sources as $source) {
        $attributes = function_exists('facuso_external_link_attributes') ? facuso_external_link_attributes($source['url']) : '';
        echo '<li><a href="' . esc_url($source['url']) . '"' . $attributes . '>' . esc_html($source['title']) . '</a></li>';
    }
    echo '</ul><p>' . esc_html(fac_theme_text('source_date')) . '</p></details>';
}
