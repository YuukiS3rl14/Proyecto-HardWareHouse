document.addEventListener('DOMContentLoaded', function() {
    // --- Lógica para el control de cantidad en el carrito ---
    const quantityForms = document.querySelectorAll('form[id^="form-"]');

    quantityForms.forEach(form => {
        const minusButton = form.querySelector('.btn-minus');
        const plusButton = form.querySelector('.btn-plus');
        const quantityInput = form.querySelector('input[name="quantity"]');

        if (minusButton && plusButton && quantityInput) {
            minusButton.addEventListener('click', function() {
                // Deshabilitar botones para evitar clics múltiples
                minusButton.disabled = true;
                plusButton.disabled = true;

                let currentValue = parseInt(quantityInput.value);
                // Restamos 1, pero no permitimos que baje de 0
                quantityInput.value = Math.max(0, currentValue - 1);
                form.submit();
            });

            plusButton.addEventListener('click', function() {
                // Deshabilitar botones para evitar clics múltiples
                minusButton.disabled = true;
                plusButton.disabled = true;

                let currentValue = parseInt(quantityInput.value);
                // Sumamos 1
                quantityInput.value = currentValue + 1;
                form.submit();
            });
        }
    });
});