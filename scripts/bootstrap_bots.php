<?php
// Configuración exclusiva de las ocho cuentas del entorno Docker local.
$_SERVER['HTTP_HOST'] = '127.0.0.1:18086';
require '/var/www/html/wp-load.php';
if (wp_get_environment_type() !== 'local' || get_option('home') !== 'http://127.0.0.1:18086') {
    throw new RuntimeException('Este guion solo admite el WordPress de pruebas.');
}
facuso_register_bot_role();
$credentials = [];
foreach (['almeria', 'cadiz', 'cordoba', 'granada', 'huelva', 'jaen', 'malaga', 'sevilla'] as $province) {
    $login = 'facuso-bot-' . $province;
    $user = get_user_by('login', $login);
    if (!$user) {
        $id = wp_insert_user(['user_login' => $login, 'user_pass' => wp_generate_password(60, true, true),
            'user_email' => $province . '@example.invalid', 'display_name' => 'FAC-USO · ' . ucfirst($province),
            'role' => 'facuso_news_bot']);
        if (is_wp_error($id)) {
            throw new RuntimeException($id->get_error_message());
        }
        $user = get_user_by('id', $id);
    }
    update_user_meta($user->ID, '_facuso_bot_province', $province);
    $key = 'facuso-local-' . $province;
    foreach (WP_Application_Passwords::get_user_application_passwords($user->ID) as $password) {
        if ($password['name'] === $key) {
            WP_Application_Passwords::delete_application_password($user->ID, $password['uuid']);
        }
    }
    $result = WP_Application_Passwords::create_new_application_password($user->ID, ['name' => $key]);
    if (is_wp_error($result)) {
        throw new RuntimeException($result->get_error_message());
    }
    $credentials[$province] = $result[0];
}
// El llamador consume este JSON por un pipe y lo guarda en secretos; no mostrarlo.
echo json_encode($credentials, JSON_THROW_ON_ERROR);
