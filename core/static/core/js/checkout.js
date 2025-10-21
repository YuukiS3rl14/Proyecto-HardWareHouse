// Alerta de compra exitosa
document.getElementById("placeOrder").addEventListener("click", function () {
    const alert = document.getElementById("checkoutAlert");
    alert.style.display = "block";
    alert.classList.add("show");
    setTimeout(() => {
        alert.classList.remove("show");
        alert.style.display = "none";
    }, 3000);
});