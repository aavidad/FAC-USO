<?php
/**
 * Provision the eight provincial REST-only users from WP-CLI.
 *
 * wp --user=<admin> eval-file provision_wordpress.php -- /private/path/bots
 * The sole argument is a private directory outside the WordPress document root.
 */

if (!defined('WP_CLI') || !WP_CLI) {
    exit(1);
}

function facuso_provision_fail(string $reason): void {
    WP_CLI::error($reason);
}

function facuso_provision_inside(string $path, string $root): bool {
    $root = rtrim($root, '/');
    return $path === $root || str_starts_with($path, $root . '/');
}

function facuso_provision_dir(string $raw): string {
    $directory = rtrim($raw, '/');
    if ($directory === '' || $directory[0] !== '/' || preg_match('~(?:^|/)(?:\.|\.\.)(?:/|$)|[\x00-\x1f]~', $directory)) {
        facuso_provision_fail('La ruta de secretos debe ser absoluta y sin componentes especiales.');
    }
    $walk = '';
    foreach (explode('/', ltrim($directory, '/')) as $part) {
        if ($part === '') {
            facuso_provision_fail('La ruta de secretos contiene un componente vacío.');
        }
        $walk .= '/' . $part;
        if (is_link($walk)) {
            facuso_provision_fail('La ruta de secretos no admite enlaces simbólicos.');
        }
    }
    $parent = realpath(dirname($directory));
    if ($parent === false || !is_dir($parent)) {
        facuso_provision_fail('Cree primero el directorio padre de los secretos.');
    }
    $canonical = rtrim($parent, '/') . '/' . basename($directory);
    $document_root = getenv('FACUSO_DOCUMENT_ROOT') ?: ($_SERVER['DOCUMENT_ROOT'] ?? '');
    if ($document_root === '' || $document_root[0] !== '/' || realpath($document_root) === false) {
        facuso_provision_fail('Indique FACUSO_DOCUMENT_ROOT con la ruta absoluta del directorio público de la web.');
    }
    $forbidden = [ABSPATH, WP_CONTENT_DIR, $document_root];
    foreach ($forbidden as $root) {
        if ($root === '') {
            continue;
        }
        $resolved = realpath($root);
        if ($resolved !== false && facuso_provision_inside($canonical, $resolved)) {
            facuso_provision_fail('Los secretos deben quedar fuera del directorio web y de WordPress.');
        }
    }
    if (file_exists($directory) || is_link($directory)) {
        if (is_link($directory) || !is_dir($directory) || (fileperms($directory) & 0777) !== 0700) {
            facuso_provision_fail('El directorio de secretos existente debe ser real y tener permisos 0700.');
        }
        if (!is_readable($directory) || !is_writable($directory)) {
            facuso_provision_fail('El usuario de WP-CLI no puede leer y escribir el directorio de secretos.');
        }
    } elseif (!is_writable($parent)) {
        facuso_provision_fail('El usuario de WP-CLI no puede crear el directorio de secretos.');
    }
    return $directory;
}

if (isset($args) && is_array($args) && ($args[0] ?? null) === '--') {
    array_shift($args);
}
if (!isset($args) || !is_array($args) || count($args) !== 1 || !is_string($args[0])) {
    facuso_provision_fail('Uso: wp --user=<admin> eval-file provision_wordpress.php -- /ruta/privada/bots');
}
if (!current_user_can('manage_options') || !current_user_can('create_users') || !current_user_can('promote_users')) {
    facuso_provision_fail('La cuenta WP-CLI requiere manage_options, create_users y promote_users.');
}
if (!function_exists('facuso_register_bot_role') || !function_exists('facuso_dimension')) {
    facuso_provision_fail('Active primero el plugin FAC-USO Arranque.');
}
$role = get_role('facuso_news_bot');
if (!$role) {
    facuso_provision_fail('No existe el rol facuso_news_bot. Reactive el plugin.');
}
$required_caps = ['read', 'edit_posts', 'edit_published_posts', 'publish_posts'];
$actual_caps = array_keys(array_filter($role->capabilities));
sort($required_caps);
sort($actual_caps);
if ($actual_caps !== $required_caps) {
    facuso_provision_fail('El rol facuso_news_bot tiene permisos inesperados.');
}
if (!function_exists('wp_is_application_passwords_available') || !wp_is_application_passwords_available()) {
    facuso_provision_fail('Habilite HTTPS y las contraseñas de aplicación en WordPress.');
}

$directory = facuso_provision_dir($args[0]);
$provinces = ['almeria', 'cadiz', 'cordoba', 'granada', 'huelva', 'jaen', 'malaga', 'sevilla'];
$plans = [];
if (is_dir($directory)) {
    $entries = scandir($directory);
    if ($entries === false) {
        facuso_provision_fail('No se pudo inspeccionar el directorio de secretos.');
    }
    foreach ($entries as $entry) {
        if ($entry !== '.' && $entry !== '..' && !in_array($entry, $provinces, true)) {
            facuso_provision_fail('El directorio de secretos contiene un archivo inesperado.');
        }
    }
}

// Inspect every province before the first write. A conflicting identity or
// secret blocks the whole run, including provinces that would otherwise work.
foreach ($provinces as $province) {
    $login = 'facuso-bot-' . $province;
    $path = $directory . '/' . $province;
    $user = get_user_by('login', $login);
    $secret_exists = file_exists($path) || is_link($path);
    if ($secret_exists) {
        if (is_link($path) || !is_file($path) || (fileperms($path) & 0777) !== 0400 || !is_readable($path)) {
            facuso_provision_fail('Un secreto existente tiene tipo o permisos inseguros: ' . $path);
        }
        $size = filesize($path);
        if ($size === false || $size < 20 || $size > 256) {
            facuso_provision_fail('Un secreto existente tiene tamaño inválido: ' . $path);
        }
    }
    if (!$user) {
        if ($secret_exists) {
            facuso_provision_fail('Hay un secreto sin cuenta de bot: ' . $path);
        }
        if (email_exists($login . '@example.invalid')) {
            facuso_provision_fail('El correo reservado para un bot ya está ocupado.');
        }
        $plans[$province] = ['mode' => 'create', 'login' => $login, 'path' => $path];
        continue;
    }
    if (count((array) $user->roles) !== 1 || !in_array('facuso_news_bot', (array) $user->roles, true)) {
        facuso_provision_fail('Un nombre de bot pertenece a otra cuenta: ' . $login);
    }
    foreach ((array) $user->caps as $cap => $granted) {
        if ($granted && $cap !== 'facuso_news_bot') {
            facuso_provision_fail('Una cuenta de bot tiene permisos directos inesperados: ' . $login);
        }
    }
    $scopes = get_user_meta($user->ID, '_facuso_bot_province', false);
    if ($scopes !== [$province]) {
        facuso_provision_fail('Una cuenta de bot tiene un ámbito provincial inesperado: ' . $login);
    }
    // Read raw metadata here: get_user_application_passwords() can repair old
    // UUIDs and would turn conflict preflight into a write.
    $apps = get_user_meta($user->ID, WP_Application_Passwords::USERMETA_KEY_APPLICATION_PASSWORDS, true);
    if ($apps === '') {
        $apps = [];
    }
    if (!is_array($apps)) {
        facuso_provision_fail('Los metadatos de credenciales del bot son inválidos: ' . $login);
    }
    if ($secret_exists) {
        if (count($apps) !== 1 || ($apps[0]['name'] ?? '') !== $login) {
            facuso_provision_fail('Un secreto existente no tiene una única credencial asociada: ' . $login);
        }
        $plain = trim((string) file_get_contents($path));
        $hash = (string) ($apps[0]['password'] ?? '');
        $matches = method_exists('WP_Application_Passwords', 'check_password')
            ? WP_Application_Passwords::check_password($plain, $hash)
            : wp_check_password($plain, $hash);
        unset($plain);
        if (!$matches) {
            facuso_provision_fail('Un secreto existente no corresponde a su bot: ' . $login);
        }
        $plans[$province] = ['mode' => 'preserve', 'login' => $login, 'path' => $path, 'id' => $user->ID];
    } else {
        if (count($apps) !== 0) {
            facuso_provision_fail('Un bot tiene una credencial sin archivo secreto: ' . $login);
        }
        $plans[$province] = ['mode' => 'credential', 'login' => $login, 'path' => $path, 'id' => $user->ID];
    }
}

$old_umask = umask(0077);
if (!is_dir($directory) && !mkdir($directory, 0700)) {
    facuso_provision_fail('No se pudo crear el directorio de secretos.');
}
if ((fileperms($directory) & 0777) !== 0700) {
    facuso_provision_fail('El directorio de secretos no tiene permisos 0700.');
}

// WP itself sends no mail here. Suppress wp_mail from other plugin callbacks
// while preserving their audit and security hooks.
add_filter('pre_wp_mail', '__return_true', PHP_INT_MAX);

$created_users = 0;
$created_credentials = 0;
$preserved = 0;
foreach ($plans as $province => $plan) {
    if ($plan['mode'] === 'preserve') {
        ++$preserved;
        continue;
    }
    $user_id = $plan['id'] ?? null;
    if ($user_id === null) {
        $user_id = wp_insert_user([
            'user_login' => $plan['login'],
            'user_pass' => wp_generate_password(64, true, true),
            'user_email' => $plan['login'] . '@example.invalid',
            'display_name' => 'FAC-USO ' . ucfirst($province),
            'role' => 'facuso_news_bot',
        ]);
        if (is_wp_error($user_id)) {
            facuso_provision_fail('No se pudo crear la cuenta provincial: ' . $plan['login']);
        }
        if (!update_user_meta($user_id, '_facuso_bot_province', $province)) {
            facuso_provision_fail('No se pudo fijar el ámbito provincial: ' . $plan['login']);
        }
        ++$created_users;
    }
    $app = WP_Application_Passwords::create_new_application_password((int) $user_id, ['name' => $plan['login']]);
    if (is_wp_error($app)) {
        facuso_provision_fail('No se pudo crear la credencial de aplicación: ' . $plan['login']);
    }
    $secret = $app[0];
    $uuid = $app[1]['uuid'];
    $handle = @fopen($plan['path'], 'x');
    if ($handle === false) {
        WP_Application_Passwords::delete_application_password((int) $user_id, $uuid);
        facuso_provision_fail('No se pudo crear el archivo exclusivo: ' . $plan['path']);
    }
    $safe = chmod($plan['path'], 0400);
    $length = strlen($secret);
    $written = 0;
    while ($safe && $written < $length) {
        $count = fwrite($handle, substr($secret, $written));
        if ($count === false || $count === 0) {
            $safe = false;
            break;
        }
        $written += $count;
    }
    $safe = $safe && $written === $length && fflush($handle);
    if ($safe && function_exists('fsync')) {
        $safe = fsync($handle);
    }
    $closed = fclose($handle);
    unset($secret);
    if (!$safe || !$closed) {
        @unlink($plan['path']);
        WP_Application_Passwords::delete_application_password((int) $user_id, $uuid);
        facuso_provision_fail('No se pudo guardar el secreto de forma segura: ' . $plan['login']);
    }
    ++$created_credentials;
}
umask($old_umask);

WP_CLI::log(wp_json_encode([
    'secret_directory' => $directory,
    'created_users' => $created_users,
    'created_credentials' => $created_credentials,
    'preserved_credentials' => $preserved,
    'files' => array_map(static fn($province) => $directory . '/' . $province, $provinces),
], JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE));
