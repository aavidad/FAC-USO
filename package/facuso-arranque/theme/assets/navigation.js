document.documentElement.classList.add('fac-js');
document.querySelectorAll('.fac-menu-toggle,.fac-sub-toggle').forEach(button => {
    button.addEventListener('click', () => {
        const target = button.classList.contains('fac-menu-toggle')
            ? document.getElementById(button.getAttribute('aria-controls'))
            : button.parentElement;
        const open = button.getAttribute('aria-expanded') !== 'true';
        button.setAttribute('aria-expanded', String(open));
        target.classList.toggle('fac-open', open);
    });
});
document.addEventListener('keydown', event => {
    if (event.key !== 'Escape') return;
    const opened = document.activeElement.closest('li.fac-open');
    if (opened) {
        opened.classList.remove('fac-open');
        const button = opened.querySelector('.fac-sub-toggle');
        button.setAttribute('aria-expanded', 'false');
        button.focus();
    }
});
