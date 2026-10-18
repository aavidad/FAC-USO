<?php
/** Adaptador CLI mínimo del aprovisionador; las mismas comprobaciones y API WP. */
declare(strict_types=1);
if (PHP_SAPI !== 'cli' || getenv('FACUSO_DOMAIN') !== 'facuso.cidonia.cloud') exit(1);
$_SERVER['HTTP_HOST'] = 'facuso.cidonia.cloud';
$_SERVER['HTTPS'] = 'on';
require '/var/www/html/wp-load.php';
if (home_url() !== 'https://facuso.cidonia.cloud' || wp_get_environment_type() !== 'staging') exit(1);
$admin = get_user_by('login', 'facuso-admin');
if (!$admin || !in_array('administrator', $admin->roles, true)) exit(1);
wp_set_current_user($admin->ID);
define('WP_CLI', true);
class WP_CLI {
    public static function error(string $reason): never { fwrite(STDERR, $reason . PHP_EOL); exit(1); }
    public static function log(string $message): void { echo $message, PHP_EOL; }
}
putenv('FACUSO_DOCUMENT_ROOT=/var/www/html');
$args = ['/private/bots'];
require '/tools/provision_wordpress.php';
