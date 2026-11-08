/* Presentación CLP. Los cálculos siguen usando el número sin separadores. */
(function () {
    'use strict';

    function hwPesos(valor) {
        var numero = Number(valor);
        if (!isFinite(numero)) {
            return '$0';
        }
        var entero = Math.round(numero);
        var signo = entero < 0 ? '-' : '';
        var texto = String(Math.abs(entero)).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
        return signo + '$' + texto;
    }

    window.hwPesos = hwPesos;
})();
