// Feedback visual compartido por todas las páginas.
(function () {
    'use strict';

    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // --- Avisos flotantes ---
    function getToastStack() {
        let stack = document.querySelector('.hw-toast-stack');
        if (!stack) {
            stack = document.createElement('div');
            stack.className = 'hw-toast-stack';
            stack.setAttribute('aria-live', 'polite');
            document.body.appendChild(stack);
        }
        return stack;
    }

    function showToast(message, type = 'success') {
        const toast = document.createElement('div');
        const isError = type === 'error';
        toast.className = 'hw-toast' + (isError ? ' is-error' : '');
        toast.setAttribute('role', isError ? 'alert' : 'status');
        toast.innerHTML = `<i class="fas ${isError ? 'fa-exclamation-circle' : 'fa-check-circle'}"></i><span></span>`;
        toast.querySelector('span').textContent = message;
        getToastStack().appendChild(toast);

        setTimeout(() => {
            toast.classList.add('is-leaving');
            toast.addEventListener('animationend', () => toast.remove(), { once: true });
        }, 3000);
    }

    // --- Animaciones puntuales ---
    function replayAnimation(el, className) {
        if (!el) return;
        el.classList.remove(className);
        void el.offsetWidth;
        el.classList.add(className);
        el.addEventListener('animationend', () => el.classList.remove(className), { once: true });
    }

    function updateCount(selector, value) {
        document.querySelectorAll(selector).forEach((el) => {
            if (value !== undefined && value !== null) el.textContent = value;
            replayAnimation(el, 'is-bumping');
        });
    }

    window.HW = {
        showToast,
        replayAnimation,
        updateCartCount: (value) => updateCount('[data-cart-count]', value),
        updateFavoriteCount: (value) => updateCount('[data-favorite-count]', value),
    };
    window.showToast = showToast;

    // --- Onda al hacer clic en botones ---
    document.addEventListener('pointerdown', (event) => {
        if (reducedMotion) return;
        const btn = event.target.closest('.btn');
        if (!btn || btn.disabled || btn.classList.contains('icon-btn') || btn.closest('.quantity')) return;

        const rect = btn.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const ripple = document.createElement('span');
        ripple.className = 'ripple';
        ripple.style.width = ripple.style.height = `${size}px`;
        ripple.style.left = `${event.clientX - rect.left - size / 2}px`;
        ripple.style.top = `${event.clientY - rect.top - size / 2}px`;
        btn.appendChild(ripple);
        ripple.addEventListener('animationend', () => ripple.remove(), { once: true });
    });

    // --- Estado "cargando" en formularios que recargan la página ---
    document.addEventListener('submit', (event) => {
        if (event.defaultPrevented) return;
        const form = event.target;
        if ((form.method || '').toLowerCase() !== 'post') return;
        const btn = event.submitter || form.querySelector('button[type="submit"], button:not([type])');
        if (btn && btn.classList.contains('btn')) {
            btn.classList.add('is-loading');
            btn.setAttribute('aria-busy', 'true');
        }
    });

    // Al volver con el botón "atrás" el navegador puede restaurar la página con el spinner activo.
    window.addEventListener('pageshow', () => {
        document.querySelectorAll('.btn.is-loading').forEach((btn) => {
            btn.classList.remove('is-loading');
            btn.removeAttribute('aria-busy');
        });
    });

    document.addEventListener('DOMContentLoaded', () => {
        // --- Selector de cantidad del detalle de producto ---
        document.querySelectorAll('.add-to-cart-form .quantity').forEach((group) => {
            const input = group.querySelector('input[name="quantity"]');
            if (!input) return;
            group.querySelectorAll('.btn-minus, .btn-plus').forEach((btn) => {
                btn.addEventListener('click', () => {
                    const current = parseInt(input.value, 10) || 1;
                    input.value = btn.classList.contains('btn-plus') ? current + 1 : Math.max(1, current - 1);
                });
            });
        });

        // --- Total del armado de PC en la barra móvil ---
        const mobileTotal = document.getElementById('mobile-total-price');
        if (mobileTotal) {
            new MutationObserver(() => replayAnimation(mobileTotal, 'is-bumping'))
                .observe(mobileTotal, { childList: true, characterData: true, subtree: true });
        }

        // --- Aparición al hacer scroll ---
        if (reducedMotion || !('IntersectionObserver' in window)) return;

        const targets = document.querySelectorAll(
            '.feature-box, .product-item, .filter-group, .card, .section-title, .media, .vendor-item, .table-stack tbody tr'
        );
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (!entry.isIntersecting) return;
                entry.target.classList.add('is-visible');
                observer.unobserve(entry.target);
            });
        }, { rootMargin: '0px 0px -40px 0px', threshold: 0.08 });

        targets.forEach((el) => {
            if (el.closest('.owl-carousel, .modal, #menuMovil')) return;
            // Las tarjetas suelen ir solas dentro de una columna; en ese caso el escalonado usa la columna.
            const item = el.parentElement && el.parentElement.children.length === 1 ? el.parentElement : el;
            const siblings = item.parentElement ? [...item.parentElement.children] : [];
            const index = Math.max(0, siblings.indexOf(item));
            el.style.transitionDelay = `${Math.min(index, 5) * 60}ms`;
            el.classList.add('reveal');
            el.addEventListener('transitionend', () => { el.style.transitionDelay = ''; }, { once: true });
            observer.observe(el);
        });
    });
})();
