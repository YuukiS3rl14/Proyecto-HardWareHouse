(function () {
    try {
    var menu = document.querySelector("#jazzy-sidebar .nav-sidebar");
    if (!menu) {
        return;
    }

    function abrir(grupo, abierto) {
        var boton = grupo.querySelector(".hw-menu-toggle");
        var lista = grupo.querySelector(".hw-menu-sub");
        if (!boton || !lista) {
            return;
        }
        grupo.classList.toggle("is-open", abierto);
        boton.setAttribute("aria-expanded", abierto ? "true" : "false");
        if (abierto) {
            lista.removeAttribute("hidden");
        } else {
            lista.setAttribute("hidden", "");
        }
    }

    var path = window.location.pathname.replace(/\/+$/, "") || "/";
    var hash = window.location.hash || "";
    var links = menu.querySelectorAll("a.nav-link[href]");
    var chosen = null;
    var chosenLength = -1;
    var hashChosen = null;
    links.forEach(function (link) {
        var href = link.getAttribute("href") || "";
        if (!href || href.charAt(0) === "#") {
            return;
        }
        var url;
        try {
            url = new URL(href, window.location.origin);
        } catch (error) {
            return;
        }
        var linkPath = url.pathname.replace(/\/+$/, "") || "/";
        var linkHash = url.hash || "";
        if (linkHash) {
            if (path === linkPath && linkHash === hash) {
                hashChosen = link;
            }
            return;
        }
        var matches = path === linkPath;
        var isHome = linkPath === "/admin";
        if (!matches && !isHome && path.indexOf(linkPath + "/") === 0) {
            matches = true;
        }
        if (matches && linkPath.length > chosenLength) {
            chosen = link;
            chosenLength = linkPath.length;
        }
    });
    if (hashChosen) {
        chosen = hashChosen;
    }
    if (chosen) {
        chosen.classList.add("active");
        chosen.setAttribute("aria-current", "page");
        var activo = chosen.closest(".hw-menu-group");
        if (activo) {
            activo.classList.add("has-active");
            abrir(activo, true);
        }
    }

    menu.querySelectorAll(".hw-menu-toggle").forEach(function (boton) {
        boton.addEventListener("click", function () {
            var grupo = boton.closest(".hw-menu-group");
            if (!grupo) {
                return;
            }
            abrir(grupo, !grupo.classList.contains("is-open"));
        });
    });
    } catch (error) {
        /* El menú no debe abortar el script: la paginación va después. */
    }
})();

(function () {
    var controles = {};
    var anclas = {
        pedidos: "hw-ultimos-pedidos",
        alertas: "hw-alertas"
    };
    var paginas = {};

    function claveDe(tarjeta) {
        return tarjeta === "pedidos" ? "pedidos_pagina" : "alertas_pagina";
    }

    function paginaDe(tarjeta) {
        return new URLSearchParams(window.location.search).get(claveDe(tarjeta)) || "1";
    }

    function recordarPaginas() {
        Object.keys(anclas).forEach(function (tarjeta) {
            paginas[tarjeta] = paginaDe(tarjeta);
        });
    }

    function seccionDe(tarjeta) {
        return document.querySelector('.hw-dashboard [data-hw-tarjeta="' + tarjeta + '"]');
    }

    function urlVisible(href, tarjeta) {
        var destino;
        try {
            destino = new URL(href, window.location.origin);
        } catch (error) {
            return null;
        }
        if (destino.origin !== window.location.origin) {
            return null;
        }
        var actual = new URL(window.location.href);
        var clave = tarjeta === "pedidos" ? "pedidos_pagina" : "alertas_pagina";
        if (destino.searchParams.has(clave)) {
            actual.searchParams.set(clave, destino.searchParams.get(clave));
        } else {
            actual.searchParams.delete(clave);
        }
        actual.searchParams.delete("hw_tarjeta");
        actual.hash = destino.hash;
        return actual;
    }

    function urlParcial(href, tarjeta) {
        var visible = urlVisible(href, tarjeta);
        if (!visible) {
            return null;
        }
        visible.searchParams.set("hw_tarjeta", tarjeta);
        visible.hash = "";
        return visible;
    }

    function marcar(seccion, activo) {
        seccion.classList.toggle("is-loading", activo);
        if (activo) {
            seccion.setAttribute("aria-busy", "true");
        } else {
            seccion.removeAttribute("aria-busy");
        }
    }

    function aviso(seccion) {
        var cuerpo = seccion.querySelector("[data-hw-cuerpo]");
        if (!cuerpo || cuerpo.querySelector(".hw-pager-error")) {
            return;
        }
        var nota = document.createElement("p");
        nota.className = "hw-pager-error";
        nota.setAttribute("role", "alert");
        nota.textContent = "No se pudo actualizar esta tarjeta. Intenta de nuevo.";
        cuerpo.appendChild(nota);
    }

    function aplicar(seccion, html, tarjeta) {
        var cuerpo = seccion.querySelector("[data-hw-cuerpo]");
        var marca = "<!-- hw-tarjeta:" + tarjeta + " -->";
        var limpio = (html || "").replace(/^\uFEFF/, "").trim();
        if (!cuerpo || limpio.indexOf(marca) !== 0) {
            throw new Error("respuesta");
        }
        cuerpo.innerHTML = limpio;
    }

    function cargar(href, tarjeta, empujar) {
        var seccion = seccionDe(tarjeta);
        var destino = urlParcial(href, tarjeta);
        if (!seccion || !destino) {
            return;
        }
        if (controles[tarjeta]) {
            controles[tarjeta].abort();
        }
        var control = new AbortController();
        controles[tarjeta] = control;
        marcar(seccion, true);
        fetch(destino.toString(), {
            method: "GET",
            credentials: "same-origin",
            headers: { "X-Requested-With": "HWDashboard" },
            signal: control.signal
        }).then(function (respuesta) {
            var final = new URL(respuesta.url, window.location.origin);
            var tipo = respuesta.headers.get("content-type") || "";
            if (!respuesta.ok || final.origin !== window.location.origin || tipo.indexOf("text/html") === -1) {
                throw new Error("respuesta");
            }
            return respuesta.text();
        }).then(function (html) {
            if (controles[tarjeta] !== control) {
                return;
            }
            var scrollX = window.scrollX;
            var scrollY = window.scrollY;
            aplicar(seccion, html, tarjeta);
            window.scrollTo(scrollX, scrollY);
            if (empujar) {
                var visible = urlVisible(href, tarjeta);
                history.pushState({ hwTarjeta: tarjeta }, "", visible.pathname + visible.search + visible.hash);
            }
            paginas[tarjeta] = paginaDe(tarjeta);
        }).catch(function (error) {
            if (error && error.name === "AbortError") {
                return;
            }
            aviso(seccion);
        }).then(function () {
            if (controles[tarjeta] === control) {
                marcar(seccion, false);
            }
        });
    }

    document.addEventListener("click", function (evento) {
        if (evento.button > 0 || evento.metaKey || evento.ctrlKey || evento.shiftKey || evento.altKey) {
            return;
        }
        var nodo = evento.target;
        var enlace = null;
        while (nodo && nodo !== document) {
            if (nodo.nodeType === 1 && nodo.tagName === "A" && nodo.classList && nodo.classList.contains("hw-pager-link")) {
                enlace = nodo;
                break;
            }
            nodo = nodo.parentNode;
        }
        if (!enlace || !enlace.closest(".hw-dashboard")) {
            return;
        }
        var seccion = enlace.closest("[data-hw-tarjeta]");
        if (!seccion) {
            return;
        }
        evento.preventDefault();
        cargar(enlace.getAttribute("href"), seccion.getAttribute("data-hw-tarjeta"), true);
    }, true);

    window.addEventListener("popstate", function () {
        Object.keys(anclas).forEach(function (tarjeta) {
            if (!seccionDe(tarjeta)) {
                return;
            }
            var nueva = paginaDe(tarjeta);
            if (nueva === paginas[tarjeta]) {
                return;
            }
            var visible = window.location.pathname + window.location.search + "#" + anclas[tarjeta];
            cargar(visible, tarjeta, false);
        });
    });

    recordarPaginas();
})();
