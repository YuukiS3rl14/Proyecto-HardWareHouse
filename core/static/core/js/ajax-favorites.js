document.addEventListener('DOMContentLoaded', function() {
    document.body.addEventListener('click', function(event) {
        if (event.target.matches('.toggle-favorite-btn, .toggle-favorite-btn *')) {
            event.preventDefault();
            const button = event.target.closest('.toggle-favorite-btn');
            
            // Si el usuario no está autenticado, redirigir al login
            if (button.dataset.isAuthenticated === 'false') {
                window.location.href = button.dataset.loginUrl;
                return;
            }

            const productId = button.dataset.productId;
            const modelName = button.dataset.modelName;
            const url = button.dataset.url;
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            const formData = new FormData();
            formData.append('product_id', productId);
            formData.append('model_name', modelName);

            fetch(url, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrfToken,
                },
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'added' || data.status === 'removed') {
                    showToast(data.message, 'success');
                    // Cambiar el ícono y texto del botón
                    const icon = button.querySelector('i');
                    if (data.status === 'added') {
                        icon.classList.remove('far');
                        icon.classList.add('fas');
                        button.title = 'Quitar de favoritos';
                    } else {
                        icon.classList.remove('fas');
                        icon.classList.add('far');
                        button.title = 'Agregar a favoritos';
                    }
                } else {
                    showToast(data.message || 'Ocurrió un error.', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('Error de conexión. Inténtalo de nuevo.', 'error');
            });
        }
    });

    // La función showToast ya existe en ajax-cart.js, así que la reutilizamos.
    // Si este archivo se carga antes, la definimos aquí también por seguridad.
    if (typeof showToast === 'undefined') {
        window.showToast = function(message, type = 'success') {
            // Implementación de showToast (copiada de ajax-cart.js si es necesario)
        };
    }
});