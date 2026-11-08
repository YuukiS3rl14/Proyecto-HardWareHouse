(function () {
    if (typeof Chart === "undefined") {
        return;
    }

    var estilo = getComputedStyle(document.documentElement);

    function variable(nombre, respaldo) {
        var valor = (estilo.getPropertyValue(nombre) || "").trim();
        return valor || respaldo;
    }

    var verde = variable("--hw-green", "#16a34a");
    var celeste = "#0284c7";
    var tinta = variable("--hw-ink", "#111827");
    var muted = variable("--hw-muted", "#6b7280");
    var cuadricula = "rgba(17, 24, 39, 0.06)";
    var coloresEstado = {
        PENDIENTE: "#c2410c",
        PAGADO: verde,
        ENVIADO: celeste,
        ENTREGADO: variable("--hw-navy", "#0f2744"),
        CANCELADO: "#b91c1c"
    };

    Chart.defaults.font.family = 'Poppins, "Segoe UI", sans-serif';
    Chart.defaults.color = muted;

    function leer(id) {
        var nodo = document.getElementById(id);
        if (!nodo) {
            return null;
        }
        return JSON.parse(nodo.textContent);
    }

    function pesos(valor) {
        return new Intl.NumberFormat("es-CL", {
            style: "currency",
            currency: "CLP",
            maximumFractionDigits: 0
        }).format(valor);
    }

    function etiquetas(puntos) {
        return puntos.map(function (punto) { return punto.etiqueta; });
    }

    function valores(puntos) {
        return puntos.map(function (punto) { return punto.valor; });
    }

    var ventas = leer("hw-grafico-ventas");
    var lienzoVentas = document.getElementById("hw-chart-ventas");
    if (ventas && lienzoVentas) {
        var montos = valores(ventas.puntos);
        new Chart(lienzoVentas, {
            type: "line",
            data: {
                labels: etiquetas(ventas.puntos),
                datasets: [{
                    label: "Ventas",
                    data: montos,
                    borderColor: verde,
                    backgroundColor: "rgba(22, 163, 74, 0.1)",
                    fill: true,
                    tension: 0.3,
                    borderWidth: 2,
                    pointRadius: 3,
                    pointHoverRadius: 5,
                    pointBackgroundColor: verde,
                    pointBorderColor: "#ffffff",
                    pointBorderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: "index", intersect: false },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function (ctx) { return pesos(ctx.parsed.y); }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        border: { display: false },
                        ticks: { autoSkip: true, maxRotation: 0, minRotation: 0, maxTicksLimit: 6, color: muted }
                    },
                    y: {
                        beginAtZero: true,
                        border: { display: false },
                        grid: { color: cuadricula },
                        ticks: {
                            color: muted,
                            maxTicksLimit: 5,
                            callback: function (valor) { return pesos(valor); }
                        }
                    }
                }
            }
        });
    }

    var estados = leer("hw-grafico-estados");
    var lienzoEstados = document.getElementById("hw-chart-estados");
    if (estados && lienzoEstados && !estados.vacio) {
        new Chart(lienzoEstados, {
            type: "doughnut",
            data: {
                labels: etiquetas(estados.puntos),
                datasets: [{
                    data: valores(estados.puntos),
                    backgroundColor: estados.puntos.map(function (punto) {
                        return coloresEstado[punto.clave] || celeste;
                    }),
                    borderColor: "#ffffff",
                    borderWidth: 3,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "68%",
                plugins: {
                    legend: {
                        position: "bottom",
                        labels: {
                            color: tinta,
                            boxWidth: 10,
                            boxHeight: 10,
                            padding: 8,
                            font: { size: 11 },
                            generateLabels: function (chart) {
                                var datos = chart.data;
                                return datos.labels.map(function (etiqueta, indice) {
                                    return {
                                        text: etiqueta + " (" + datos.datasets[0].data[indice] + ")",
                                        fillStyle: datos.datasets[0].backgroundColor[indice],
                                        strokeStyle: "#ffffff",
                                        lineWidth: 1,
                                        hidden: false,
                                        index: indice
                                    };
                                });
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function (ctx) {
                                return ctx.label + ": " + ctx.parsed + " pedidos";
                            }
                        }
                    }
                }
            }
        });
    }

})();
