<?php
/** Muestra pública existente: sin cuentas, escrituras, peticiones ni resultados almacenados. */
if (!defined('ABSPATH')) exit;
add_action('wp_enqueue_scripts', function () {
    if (is_singular() && has_shortcode((string)get_post_field('post_content', get_queried_object_id()), 'facuso_muestra_tcae')) {
        wp_enqueue_style('facuso-muestra-tcae', plugins_url('muestra-tcae.css', __FILE__), [], '1.0');
    }
});
add_shortcode('facuso_muestra_tcae', function () {
    $data = json_decode(file_get_contents(__DIR__ . '/muestra-tcae.json'), true);
    if (!is_array($data) || count($data['questions'] ?? []) !== 6) return '';
    wp_enqueue_script('facuso-muestra-tcae', plugins_url('muestra-tcae.js', __FILE__), [], '1.0', true);
    wp_enqueue_style('facuso-muestra-tcae', plugins_url('muestra-tcae.css', __FILE__), [], '1.0');
    $id = wp_unique_id('fac-tcae-');
    $labels = $data['labels'];
    $html = '<section class="fac-tcae" id="' . esc_attr($id) . '" data-labels="' . esc_attr(wp_json_encode($labels)) . '"><h2>' . esc_html($data['title']) . '</h2><p>' . esc_html($data['intro']) . '</p>';
    foreach ($data['questions'] as $i => $q) {
        $html .= '<fieldset data-correct="' . (int)$q['correct'] . '"><legend>' . esc_html($q['question']) . '</legend>';
        foreach ($q['options'] as $j => $option) {
            $html .= '<label><input type="radio" name="' . esc_attr($id . '-' . $i) . '" value="' . (int)$j . '"><span>' . esc_html($option) . '</span></label>';
        }
        // Las explicaciones y anclas son las de las seis preguntas ya públicas.
        $fragment = in_array($q['source'], ['#1-la-constitucion-como-norma-suprema', '#2-estructura-de-la-constitucion', '#3-principios-basicos-del-titulo-preliminar'], true) ? $q['source'] : '';
        $html .= '<div class="fac-tcae-feedback" hidden><strong></strong><p>' . esc_html($q['explanation']) . '</p><blockquote>' . esc_html($q['fragment']) . '</blockquote><a href="' . esc_url('https://uso.dipgra.cloud/tests' . $fragment) . '" target="_blank" rel="noopener noreferrer">' . esc_html($labels['source']) . '</a></div></fieldset>';
    }
    return $html . '<p class="fac-tcae-result" role="status" aria-live="polite"></p><button type="button" data-tcae-check hidden>' . esc_html($labels['check']) . '</button> <button type="button" data-tcae-reset hidden>' . esc_html($labels['reset']) . '</button><noscript><p>' . esc_html($labels['noscript']) . '</p></noscript></section>';
});
