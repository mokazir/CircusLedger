document.addEventListener('DOMContentLoaded', () => {
    const active = document.querySelector('.active');

    active?.setAttribute('aria-current', 'page');
})