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
            const icon = button.querySelector('i');

            const formData = new FormData();
            formData.append('product_id', productId);
            formData.append('model_name', modelName);

            HW.replayAnimation(icon, 'is-popping');
            button.disabled = true;

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
                    HW.showToast(data.message, 'success');
                    HW.updateFavoriteCount(data.favorite_count);
                    // Cambiar el ícono y texto del botón
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
                    HW.showToast(data.message || 'Ocurrió un error.', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                HW.showToast('Error de conexión. Inténtalo de nuevo.', 'error');
            })
            .finally(() => {
                button.disabled = false;
            });
        }
    });
});
