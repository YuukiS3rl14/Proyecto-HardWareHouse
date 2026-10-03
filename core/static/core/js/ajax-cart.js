document.addEventListener('DOMContentLoaded', function() {
    // Seleccionamos todos los formularios para agregar al carrito
    const addToCartForms = document.querySelectorAll('form.add-to-cart-form');

    addToCartForms.forEach(form => {
        form.addEventListener('submit', function(event) {
            // Prevenimos el envío normal del formulario
            event.preventDefault();

            const formData = new FormData(form);
            const url = form.action;
            const submitButton = event.submitter || form.querySelector('button[type="submit"]');
            if (submitButton) submitButton.classList.add('is-loading');

            fetch(url, {
                method: 'POST',
                body: formData,
                headers: {
                    // Este header es clave para que Django sepa que es una petición AJAX
                    'X-Requested-With': 'XMLHttpRequest',
                },
            })
            .then(response => {
                // @login_required redirige a la página de login en vez de responder JSON.
                if (response.redirected && response.url.includes('/login')) {
                    const loginUrl = new URL(response.url);
                    loginUrl.searchParams.set('next', window.location.pathname + window.location.search);
                    window.location.href = loginUrl.toString();
                    return null;
                }
                return response.json();
            })
            .then(data => {
                if (!data) return;
                if (data.status === 'success') {
                    HW.showToast(data.message);
                    HW.updateCartCount(data.cart_count);
                } else {
                    HW.showToast(data.message || 'Ocurrió un error.', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                HW.showToast('Error de conexión. Inténtalo de nuevo.', 'error');
            })
            .finally(() => {
                if (submitButton) submitButton.classList.remove('is-loading');
            });
        });
    });
});
