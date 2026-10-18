<?php
/** Enlaces externos del sitio público FAC-USO. */
defined('ABSPATH') || exit;

/**
 * Clasifica URL navegables: true externas, false internas y null para otros esquemas.
 */
function facuso_external_link_kind(string $url): ?bool {
    $url = trim($url);
    if ($url === '' || $url[0] === '#') {
        return null;
    }
    if (!preg_match('~^(?:https?:)?//~i', $url)) {
        return preg_match('~^[a-z][a-z0-9+.-]*:~i', $url) ? null : false;
    }

    $home = wp_parse_url(home_url('/'));
    if (!is_array($home) || empty($home['host'])) {
        return null;
    }
    if (str_starts_with($url, '//')) {
        $url = ($home['scheme'] ?? 'https') . ':' . $url;
    }
    $link = wp_parse_url($url);
    if (!is_array($link) || empty($link['host']) || !in_array(strtolower($link['scheme'] ?? ''), ['http', 'https'], true)) {
        return null;
    }

    $port = static fn(array $parts): int => (int) ($parts['port'] ?? (strtolower($parts['scheme'] ?? '') === 'https' ? 443 : 80));
    return strtolower($link['scheme']) !== strtolower($home['scheme'] ?? '')
        || strtolower($link['host']) !== strtolower($home['host'])
        || $port($link) !== $port($home);
}

/** Atributos ya escapados para anclas manuales del tema. */
function facuso_external_link_attributes(string $url): string {
    return facuso_external_link_kind($url) === true ? ' target="_blank" rel="noopener noreferrer"' : '';
}

function facuso_external_links_public_request(): bool {
    return !is_admin() && !is_feed() && !(defined('REST_REQUEST') && REST_REQUEST);
}

/** Conserva las relaciones existentes y añade protección al abrir pestaña. */
function facuso_external_link_rel(string $existing): string {
    $tokens = preg_split('/\s+/', trim($existing), -1, PREG_SPLIT_NO_EMPTY) ?: [];
    $seen = array_fill_keys(array_map('strtolower', $tokens), true);
    foreach (['noopener', 'noreferrer'] as $required) {
        if (!isset($seen[$required])) {
            $tokens[] = $required;
        }
    }
    return implode(' ', $tokens);
}

add_filter('the_content', function ($html) {
    if (!facuso_external_links_public_request() || !is_string($html) || stripos($html, '<a') === false) {
        return $html;
    }
    $processor = new WP_HTML_Tag_Processor($html);
    while ($processor->next_tag(['tag_name' => 'A'])) {
        $url = $processor->get_attribute('href');
        if (!is_string($url)) {
            continue;
        }
        $kind = facuso_external_link_kind($url);
        if ($kind === true) {
            $processor->set_attribute('target', '_blank');
            $processor->set_attribute('rel', facuso_external_link_rel((string) $processor->get_attribute('rel')));
        } elseif ($kind === false) {
            $processor->remove_attribute('target');
        }
    }
    return $processor->get_updated_html();
}, 99);

add_filter('nav_menu_link_attributes', function (array $attrs): array {
    if (!facuso_external_links_public_request() || !isset($attrs['href'])) {
        return $attrs;
    }
    $kind = facuso_external_link_kind((string) $attrs['href']);
    if ($kind === true) {
        $attrs['target'] = '_blank';
        $attrs['rel'] = facuso_external_link_rel((string) ($attrs['rel'] ?? ''));
    } elseif ($kind === false) {
        unset($attrs['target']);
    }
    return $attrs;
}, 99);

add_action('wp_enqueue_scripts', function (): void {
    if (!facuso_external_links_public_request()) {
        return;
    }
    wp_enqueue_script('facuso-external-links', plugins_url('external-links.js', __FILE__), [], '1.0.0', true);
    wp_add_inline_script(
        'facuso-external-links',
        'window.facusoExternalLinksHome=' . wp_json_encode(home_url('/'), JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT) . ';',
        'before'
    );
});
