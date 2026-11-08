(function () {
    var menu = document.querySelector("#jazzy-sidebar .nav-sidebar");
    if (!menu) {
        return;
    }
    var path = window.location.pathname.replace(/\/+$/, "") || "/";
    var links = menu.querySelectorAll("a.nav-link[href]");
    var chosen = null;
    var chosenLength = -1;
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
    if (!chosen) {
        return;
    }
    chosen.classList.add("active");
    chosen.setAttribute("aria-current", "page");
})();
