<?php defined('ABSPATH') || exit; ?>
<!doctype html>
<html <?php language_attributes(); ?>>
<head>
    <meta charset="<?php bloginfo('charset'); ?>">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="icon" type="image/png" href="<?php echo esc_url(get_template_directory_uri() . '/assets/favicon.png'); ?>">
    <?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
<?php wp_body_open(); ?>
<a class="skip-link" href="#contenido"><?php echo esc_html(fac_theme_text('skip')); ?></a>
<div class="fac-top"><div class="fac-wrap"><span><?php echo esc_html(fac_theme_text('topline')); ?></span><a href="<?php echo esc_url(fac_theme_page('contacto')); ?>"><?php echo esc_html(fac_theme_text('contact')); ?></a></div></div>
<header class="fac-header fac-wrap">
    <div class="fac-brand-row">
        <img class="fac-flag" width="250" height="167" src="<?php echo esc_url(get_template_directory_uri() . '/assets/bandera-andalucia.png'); ?>" alt="<?php echo esc_attr(fac_theme_text('flag')); ?>">
        <a class="fac-brand" href="<?php echo esc_url(home_url('/')); ?>"><img width="675" height="115" src="<?php echo esc_url(get_template_directory_uri() . '/assets/logo-facuso-andalucia.png'); ?>" alt="<?php echo esc_attr(get_bloginfo('name')); ?>"></a>
        <?php $context = fac_theme_context(); if ($context) : ?>
            <div class="fac-context">
                <?php if ($context['image']) : ?><img width="100" height="100" src="<?php echo esc_url($context['image']); ?>" alt="<?php echo esc_attr($context['title']); ?>"><?php endif; ?>
                <span><?php echo esc_html($context['title']); ?></span>
            </div>
        <?php endif; ?>
    </div>
    <button class="fac-menu-toggle" type="button" aria-controls="fac-main-nav" aria-expanded="false"><?php echo esc_html(fac_theme_text('menu')); ?></button>
    <nav class="fac-navigation" id="fac-main-nav" aria-label="<?php echo esc_attr(fac_theme_text('navigation')); ?>">
        <?php wp_nav_menu(['theme_location' => 'primary', 'container' => false, 'fallback_cb' => false, 'walker' => new Facuso_Menu_Walker()]); ?>
    </nav>
</header>
