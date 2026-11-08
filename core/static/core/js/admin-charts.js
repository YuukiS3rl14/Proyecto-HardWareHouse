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

    function leer(raiz, id) {
        var nodo = raiz.querySelector("#" + id);
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

    function ejesPesos() {
        return {
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
        };
    }

    window.hwIniciarGraficos = function (raiz) {
        raiz = raiz || document;

        var ventas = leer(raiz, "hw-grafico-ventas");
        var lienzoVentas = raiz.querySelector("#hw-chart-ventas");
        if (ventas && lienzoVentas && !Chart.getChart(lienzoVentas)) {
            new Chart(lienzoVentas, {
                type: "line",
                data: {
                    labels: etiquetas(ventas.puntos),
                    datasets: [{
                        label: "Ventas",
                        data: valores(ventas.puntos),
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
                                title: function (items) { return items.length ? items[0].label : ""; },
                                label: function (ctx) { return pesos(ctx.parsed.y); }
                            }
                        }
                    },
                    scales: ejesPesos()
                }
            });
        }

        var estados = leer(raiz, "hw-grafico-estados");
        var lienzoEstados = raiz.querySelector("#hw-chart-estados");
        if (estados && lienzoEstados && !estados.vacio && !Chart.getChart(lienzoEstados)) {
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

        var categorias = leer(raiz, "hw-grafico-categorias");
        var lienzoCategorias = raiz.querySelector("#hw-chart-categorias");
        if (categorias && lienzoCategorias && !Chart.getChart(lienzoCategorias)) {
            new Chart(lienzoCategorias, {
                type: "bar",
                data: {
                    labels: etiquetas(categorias.puntos),
                    datasets: [{
                        label: "Ingresos",
                        data: valores(categorias.puntos),
                        backgroundColor: verde,
                        borderRadius: 6,
                        maxBarThickness: 18
                    }]
                },
                options: {
                    indexAxis: "y",
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: function (ctx) { return pesos(ctx.parsed.x); }
                            }
                        }
                    },
                    scales: {
                        x: ejesPesos().y,
                        y: {
                            grid: { display: false },
                            border: { display: false },
                            ticks: { color: tinta, font: { size: 11 } }
                        }
                    }
                }
            });
        }

        var unidades = leer(raiz, "hw-grafico-unidades");
        var lienzoUnidades = raiz.querySelector("#hw-chart-unidades");
        if (unidades && lienzoUnidades && !Chart.getChart(lienzoUnidades)) {
            new Chart(lienzoUnidades, {
                type: "bar",
                data: {
                    labels: etiquetas(unidades.puntos),
                    datasets: [{
                        label: "Unidades",
                        data: valores(unidades.puntos),
                        backgroundColor: celeste,
                        borderRadius: 6,
                        maxBarThickness: 22
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: function (ctx) { return ctx.parsed.y + " unidades"; }
                            }
                        }
                    },
                    scales: {
                        x: ejesPesos().x,
                        y: {
                            beginAtZero: true,
                            border: { display: false },
                            grid: { color: cuadricula },
                            ticks: { color: muted, precision: 0, maxTicksLimit: 5 }
                        }
                    }
                }
            });
        }
    };

    window.hwIniciarGraficos(document);
})();
