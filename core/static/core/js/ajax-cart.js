document.addEventListener('DOMContentLoaded', function() {
    // Seleccionamos todos los formularios para agregar al carrito
    const addToCartForms = document.querySelectorAll('form.add-to-cart-form');

    addToCartForms.forEach(form => {
        form.addEventListener('submit', function(event) {
            // Prevenimos el envío normal del formulario
            event.preventDefault();

            const formData = new FormData(form);
            const url = form.action;

            fetch(url, {
                method: 'POST',
                body: formData,
                headers: {
                    // Este header es clave para que Django sepa que es una petición AJAX
                    'X-Requested-With': 'XMLHttpRequest',
                },
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Mostramos el mensaje de éxito
                    showToast(data.message);
                } else {
                    // Mostramos un mensaje de error si algo falla
                    showToast(data.message || 'Ocurrió un error.', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('Error de conexión. Inténtalo de nuevo.', 'error');
            });
        });
    });

    // Función para mostrar un mensaje flotante (toast)
    function showToast(message, type = 'success') {
        const toastContainer = document.body;
        const toast = document.createElement('div');
        toast.className = `alert alert-${type === 'success' ? 'success' : 'danger'} position-fixed`;
        toast.style.bottom = '20px';
        toast.style.right = '20px';
        toast.style.zIndex = '1050';
        toast.style.boxShadow = '0 4px 8px rgba(0,0,0,0.1)';
        toast.textContent = message;

        toastContainer.appendChild(toast);

        // El mensaje desaparece después de 3 segundos
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }
});