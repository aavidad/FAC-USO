/* Práctica local: no cookies, almacenamiento, envíos ni acceso al área privada. */
'use strict';
document.querySelectorAll('.fac-tcae').forEach(root => {
    const labels = JSON.parse(root.dataset.labels);
    const cards = [...root.querySelectorAll('fieldset')];
    const check = root.querySelector('[data-tcae-check]');
    const reset = root.querySelector('[data-tcae-reset]');
    const result = root.querySelector('[role=status]');
    check.hidden = false;
    check.addEventListener('click', () => {
        let score = 0;
        cards.forEach(card => {
            const selected = card.querySelector('input:checked');
            const correct = card.dataset.correct;
            const ok = selected && selected.value === correct;
            if (ok) score++;
            card.querySelectorAll('input').forEach(input => {
                input.disabled = true;
                input.closest('label').classList.toggle('is-correct', input.value === correct);
                input.closest('label').classList.toggle('is-wrong', input.checked && !ok);
            });
            const feedback = card.querySelector('.fac-tcae-feedback');
            feedback.hidden = false;
            feedback.querySelector('strong').textContent = !selected ? labels.unanswered : (ok ? labels.correct : labels.incorrect);
        });
        result.textContent = `${labels.result}: ${score} / ${cards.length}`;
        check.hidden = true;
        reset.hidden = false;
        result.scrollIntoView({block: 'center', behavior: 'smooth'});
    });
    reset.addEventListener('click', () => {
        cards.forEach(card => {
            card.querySelectorAll('input').forEach(input => {input.disabled = false; input.checked = false; input.closest('label').classList.remove('is-correct', 'is-wrong');});
            card.querySelector('.fac-tcae-feedback').hidden = true;
        });
        result.textContent = '';
        check.hidden = false;
        reset.hidden = true;
        cards[0].querySelector('input').focus();
    });
});
