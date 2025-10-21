// Botones de cantidad
document.querySelectorAll('.btn-plus').forEach(btn => {
    btn.addEventListener('click', function () {
        const input = this.parentElement.previousElementSibling;
        input.value = parseInt(input.value) + 1;
        updateTotals();
    });
});

document.querySelectorAll('.btn-minus').forEach(btn => {
    btn.addEventListener('click', function () {
        const input = this.parentElement.nextElementSibling;
        if (parseInt(input.value) > 1) input.value = parseInt(input.value) - 1;
        updateTotals();
    });
});

function updateTotals() {
    let subtotal = 0;
    document.querySelectorAll('#cart-body tr').forEach(row => {
        const price = parseInt(row.children[1].innerText.replace(/\D/g, ''));
        const qty = parseInt(row.querySelector('input').value);
        const total = price * qty;
        row.querySelector('.item-total').innerText = '$' + total.toLocaleString('es-CL');
        subtotal += total;
    });
    document.getElementById('subtotal').innerText = '$' + subtotal.toLocaleString('es-CL');
    document.getElementById('total').innerText = '$' + (subtotal + 10000).toLocaleString('es-CL');
}

// Popup
const popupBg = document.getElementById('popup-bg');
document.getElementById('checkout').addEventListener('click', function () {
    popupBg.style.display = 'flex';
});
function closePopup() {
    popupBg.style.display = 'none';
}