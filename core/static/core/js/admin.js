(function () {
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
})();
