<?php defined('ABSPATH') || exit; get_header(); ?>
<main id="contenido" class="fac-wrap">
<?php if (is_singular()) : while (have_posts()) : the_post(); ?>
    <article <?php post_class(is_front_page() ? 'fac-home' : 'fac-article'); ?>>
        <?php if (!is_front_page()) : ?>
            <nav class="fac-breadcrumb" aria-label="<?php echo esc_attr(fac_theme_text('breadcrumb')); ?>"><a href="<?php echo esc_url(home_url('/')); ?>"><?php echo esc_html(fac_theme_text('home')); ?></a>
            <?php foreach (array_reverse(get_post_ancestors(get_the_ID())) as $ancestor) : ?> / <a href="<?php echo esc_url(get_permalink($ancestor)); ?>"><?php echo esc_html(get_the_title($ancestor)); ?></a><?php endforeach; ?></nav>
            <header class="fac-page-heading"><p class="fac-eyebrow"><?php echo esc_html(is_singular('post') ? fac_theme_text('news') : fac_theme_text('federation')); ?></p><h1><?php the_title(); ?></h1>
            <?php if (is_singular('post')) : ?><p class="fac-meta"><?php echo esc_html(get_the_date()); ?></p><?php endif; ?></header>
        <?php endif; ?>
        <?php if (is_singular('post') && function_exists('facuso_image_for_post')) : $photo = facuso_image_for_post(get_the_ID()); if ($photo) : ?>
            <figure class="fac-article-photo"><img width="1280" height="720" decoding="async" src="<?php echo esc_url($photo['url']); ?>" alt="<?php echo esc_attr($photo['alt']); ?>"><figcaption><?php echo esc_html($photo['credit']); ?></figcaption></figure>
        <?php endif; endif; ?>
        <div class="fac-content"><?php the_content(); ?></div>
        <?php fac_theme_sources(); ?>
    </article>
<?php endwhile; else : ?>
    <header class="fac-page-heading"><h1><?php
    if (is_search()) { echo esc_html(sprintf(fac_theme_text('search_title'), get_search_query())); }
    elseif (is_archive()) { the_archive_title(); }
    elseif (is_404()) { echo esc_html(fac_theme_text('not_found')); }
    else { echo esc_html(fac_theme_text('news')); }
    ?></h1></header>
    <?php if (have_posts()) : ?><div class="fac-grid">
    <?php while (have_posts()) : the_post(); ?><article class="fac-card">
    <?php if (function_exists('facuso_image_for_post')) : $photo = facuso_image_for_post(get_the_ID()); if ($photo) : ?><a class="fac-card-photo" href="<?php the_permalink(); ?>" tabindex="-1" aria-hidden="true"><img width="1280" height="720" loading="lazy" src="<?php echo esc_url($photo['url']); ?>" alt=""><span><?php echo esc_html($photo['credit']); ?></span></a><?php endif; endif; ?>
    <div class="fac-card-body"><p class="fac-meta"><?php echo esc_html(get_the_date()); ?></p><h2><a href="<?php the_permalink(); ?>"><?php the_title(); ?></a></h2><?php the_excerpt(); ?></div></article><?php endwhile; ?>
    </div><?php the_posts_pagination(); else : ?><p><?php echo esc_html(fac_theme_text('no_results')); ?></p><?php get_search_form(); endif; ?>
<?php endif; ?>
</main>
<?php get_footer(); ?>
