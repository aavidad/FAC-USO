<?php defined('ABSPATH') || exit; ?>
<footer class="fac-footer"><div class="fac-wrap">
    <div class="fac-footer-top"><div><p class="fac-footer-brand"><?php echo esc_html(get_bloginfo('name')); ?></p><p><?php echo esc_html(fac_theme_text('footer_description')); ?></p></div>
    <a class="fac-button" href="<?php echo esc_url(fac_theme_page('afiliacion')); ?>"><?php echo esc_html(fac_theme_text('join')); ?></a></div>
    <nav aria-label="<?php echo esc_attr(fac_theme_text('footer_navigation')); ?>"><?php wp_nav_menu(['theme_location' => 'footer', 'container' => false, 'fallback_cb' => false]); ?></nav>
    <p class="fac-footer-note"><?php echo esc_html(fac_theme_text('footer_note')); ?></p>
</div></footer>
<?php wp_footer(); ?>
</body></html>
