<?php
/** Retira solo duplicados automáticos de un snapshot importado, conservando el original. */
declare(strict_types=1);
if (PHP_SAPI !== 'cli' || getenv('FACUSO_DOMAIN') !== 'facuso.cidonia.cloud') exit(1);
$_SERVER['HTTPS'] = 'on';
require '/var/www/html/wp-load.php';
if (home_url() !== 'https://facuso.cidonia.cloud' || wp_get_environment_type() !== 'staging') exit(1);
$admin = get_user_by('login', 'facuso-admin');
if (!$admin) exit(1);
wp_set_current_user($admin->ID);
$retired = [];
foreach (facuso_data()['posts'] as $item) {
    if (empty($item['external_id']) || $item['external_id'] !== $item['slug']) continue;
    $canonical = get_page_by_path($item['slug'], OBJECT, 'post');
    if (!$canonical || get_post_meta($canonical->ID, '_facuso_key', true) !== $item['slug']) continue;
    $source = get_post_meta($canonical->ID, 'facuso_source_url', true);
    if (!$source || $source !== ($item['sources'][0]['url'] ?? '')) continue;
    $others = get_posts(['post_type'=>'post','post_status'=>['publish','draft'],'numberposts'=>-1,
                         'meta_key'=>'facuso_source_url','meta_value'=>$source]);
    foreach ($others as $post) {
        if ($post->ID === $canonical->ID || get_post_meta($post->ID, '_facuso_key', true)) continue;
        $user = get_userdata($post->post_author);
        if (!$user || !in_array('facuso_news_bot', $user->roles, true)) continue;
        $province = get_user_meta($user->ID, '_facuso_bot_province', true);
        if (!in_array($province, $item['categories'], true)) continue;
        if ($source !== get_post_meta($post->ID, 'facuso_source_url', true)) continue;
        if ($post->post_title !== $canonical->post_title) continue;
        if (wp_trash_post($post->ID)) $retired[] = $post->ID;
    }
}
echo wp_json_encode(['duplicate_bot_posts_moved_to_trash'=>$retired,'published_posts'=>(int)wp_count_posts('post')->publish]), PHP_EOL;
