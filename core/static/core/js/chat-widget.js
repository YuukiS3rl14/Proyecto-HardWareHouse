(function () {
    'use strict';

    const SIZE_CLASSES = ['hw-chat-size--compact', 'hw-chat-size--expanded', 'hw-chat-size--fullscreen'];

    function getCookie(name) {
        const match = document.cookie.match(new RegExp('(?:^|; )' + name + '=([^;]*)'));
        return match ? decodeURIComponent(match[1]) : '';
    }

    function escapeHtml(text) {
        return String(text)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

    function formatoClp(valor) {
        const n = Number(valor);
        if (Number.isNaN(n)) {
            return '—';
        }
        return '$' + n.toLocaleString('es-CL');
    }

    function linkifySafe(container, text) {
        const p = document.createElement('p');
        p.className = 'hw-chat-bubble-text';
        const parts = String(text).split(/(\/[\w\-./?#=&%]+)/g);
        parts.forEach(function (part) {
            if (/^\/[\w\-./?#=&%]+$/.test(part)) {
                const a = document.createElement('a');
                a.href = part;
                a.textContent = part;
                p.appendChild(a);
            } else if (part) {
                p.appendChild(document.createTextNode(part));
            }
        });
        container.appendChild(p);
    }

    function init() {
        const root = document.getElementById('hw-chat-root');
        if (!root) {
            return;
        }

        const apiUrl = root.getAttribute('data-chat-url');
        const revalidarUrl = root.getAttribute('data-revalidar-url');
        const userKey = root.getAttribute('data-user-key') || 'anon';
        const panel = root.querySelector('.hw-chat-panel');
        const messagesEl = root.querySelector('.hw-chat-messages');
        const form = root.querySelector('.hw-chat-form');
        const input = root.querySelector('.hw-chat-input');
        const sendBtn = root.querySelector('.hw-chat-send');
        const launcher = root.querySelector('.hw-chat-launcher');
        const closeBtn = root.querySelector('.hw-chat-close');
        const resizeHandle = root.querySelector('.hw-chat-resize-handle');
        const sizeButtons = root.querySelectorAll('.hw-chat-size-toggle');

        const sessionApi = window.HWChatSession;
        const sessionState = sessionApi ? sessionApi.load(userKey) : null;
        const history = sessionState && sessionState.history ? sessionState.history.slice() : [];
        let buildContext = sessionState ? sessionState.buildContext : null;
        let displayLog = sessionState && sessionState.displayLog ? sessionState.displayLog.slice() : [];
        let openedOnce = displayLog.length > 0;
        let restoringSession = displayLog.length > 0;
        let persistTimer = null;

        function persistSession(partial) {
            if (!sessionApi) {
                return;
            }
            clearTimeout(persistTimer);
            persistTimer = setTimeout(function () {
                sessionApi.save(
                    Object.assign(
                        {
                            history: history,
                            displayLog: displayLog,
                            buildContext: buildContext,
                            open: root.classList.contains('is-open'),
                            panelSize: root.classList.contains('hw-chat-size--fullscreen')
                                ? 'fullscreen'
                                : root.classList.contains('hw-chat-size--expanded')
                                  ? 'expanded'
                                  : 'compact',
                        },
                        partial || {}
                    ),
                    userKey
                );
            }, 180);
        }

        function setPanelSize(size) {
            const mode = size === 'expanded' || size === 'fullscreen' ? size : 'compact';
            SIZE_CLASSES.forEach(function (cls) {
                root.classList.remove(cls);
            });
            root.classList.add('hw-chat-size--' + mode);
            sizeButtons.forEach(function (btn) {
                const pressed = btn.getAttribute('data-size') === mode;
                btn.setAttribute('aria-pressed', pressed ? 'true' : 'false');
            });
            persistSession({ panelSize: mode });
        }

        function restorePanelSize() {
            const saved =
                sessionState && sessionState.panelSize ? sessionState.panelSize : 'compact';
            if (saved === 'compact' || saved === 'expanded' || saved === 'fullscreen') {
                setPanelSize(saved);
                return;
            }
            setPanelSize('compact');
        }

        async function fetchProductosRevalidados(componentes) {
            if (!revalidarUrl || !componentes || !componentes.length) {
                return null;
            }
            try {
                const response = await fetch(revalidarUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken'),
                    },
                    credentials: 'same-origin',
                    body: JSON.stringify({ componentes: componentes }),
                });
                const data = await response.json().catch(function () {
                    return {};
                });
                if (!response.ok || !data.productos) {
                    return null;
                }
                return data;
            } catch (e) {
                return null;
            }
        }

        function maybeAutoExpandForUi(ui) {
            if (!ui) {
                return;
            }
            const count = (ui.products && ui.products.length) || (ui.orders && ui.orders.length) || 0;
            if (count >= 3 && !root.classList.contains('hw-chat-size--fullscreen')) {
                setPanelSize('expanded');
            }
        }

        function autoResizeInput() {
            input.style.height = 'auto';
            const max = 120;
            input.style.height = Math.min(input.scrollHeight, max) + 'px';
        }

        function resetInputHeight() {
            input.style.height = '';
            autoResizeInput();
        }

        function setOpen(open) {
            root.classList.toggle('is-open', open);
            root.setAttribute('aria-hidden', open ? 'false' : 'true');
            launcher.setAttribute('aria-expanded', open ? 'true' : 'false');
            persistSession({ open: open });
            if (open && !openedOnce) {
                openedOnce = true;
                appendBotMessage(
                    {
                        reply: root.getAttribute('data-welcome') || '¡Hola! ¿En qué te ayudo?',
                    },
                    { skipPersist: false }
                );
            }
            if (open) {
                if (
                    !restoringSession &&
                    window.matchMedia('(max-width: 575.98px)').matches &&
                    !(sessionState && sessionState.panelSize)
                ) {
                    setPanelSize('fullscreen');
                }
                setTimeout(function () {
                    input.focus();
                    autoResizeInput();
                }, 220);
            }
            if (sessionApi) {
                sessionApi.touch(userKey);
            }
        }

        function scrollMessagesToEnd() {
            messagesEl.scrollTop = messagesEl.scrollHeight;
        }

        function pushHistory(role, content) {
            history.push({ role: role, content: content });
            if (history.length > 20) {
                history.shift();
            }
        }

        function appendUserMessage(text, options) {
            const skipPersist = options && options.skipPersist;
            const bubble = document.createElement('div');
            bubble.className = 'hw-chat-bubble hw-chat-bubble--user';
            bubble.setAttribute('role', 'article');
            bubble.textContent = text;
            messagesEl.appendChild(bubble);
            scrollMessagesToEnd();
            pushHistory('user', text);
            if (!skipPersist) {
                displayLog.push({ role: 'user', content: text });
                persistSession({});
            }
        }

        function renderProductsUi(parent, products) {
            if (!products || !products.length) {
                return;
            }
            const block = document.createElement('div');
            block.className = 'hw-chat-ui-block';

            const tableWrap = document.createElement('div');
            tableWrap.className = 'hw-chat-table-wrap';
            const table = document.createElement('table');
            table.className = 'hw-chat-table';
            const thead = document.createElement('thead');
            const headRow = document.createElement('tr');
            ['Producto', 'Precio', 'Stock', ''].forEach(function (label) {
                const th = document.createElement('th');
                th.scope = 'col';
                th.textContent = label;
                headRow.appendChild(th);
            });
            thead.appendChild(headRow);
            table.appendChild(thead);

            const tbody = document.createElement('tbody');
            products.forEach(function (item) {
                const tr = document.createElement('tr');
                const nombre = item.nombre_completo || item.nombre || 'Producto';
                const tdName = document.createElement('td');
                tdName.textContent = nombre;
                const tdPrice = document.createElement('td');
                tdPrice.textContent = formatoClp(item.precio_clp);
                const tdStock = document.createElement('td');
                const stock = Number(item.stock);
                tdStock.textContent = String(stock);
                tdStock.className = stock > 0 ? 'hw-chat-stock--ok' : 'hw-chat-stock--no';
                const tdLink = document.createElement('td');
                if (item.url_detalle) {
                    const a = document.createElement('a');
                    a.href = item.url_detalle;
                    a.textContent = 'Ver';
                    a.className = 'hw-chat-card-link';
                    tdLink.appendChild(a);
                }
                tr.appendChild(tdName);
                tr.appendChild(tdPrice);
                tr.appendChild(tdStock);
                tr.appendChild(tdLink);
                tbody.appendChild(tr);
            });
            table.appendChild(tbody);
            tableWrap.appendChild(table);
            block.appendChild(tableWrap);

            const cards = document.createElement('div');
            cards.className = 'hw-chat-cards';
            products.forEach(function (item) {
                const card = document.createElement('article');
                card.className = 'hw-chat-card';
                const title = document.createElement('p');
                title.className = 'hw-chat-card-title';
                title.textContent = item.nombre_completo || item.nombre || 'Producto';
                const meta = document.createElement('p');
                meta.className = 'hw-chat-card-meta';
                meta.textContent =
                    formatoClp(item.precio_clp) +
                    ' CLP · Stock ' +
                    String(item.stock) +
                    (item.categoria ? ' · ' + item.categoria : '');
                card.appendChild(title);
                card.appendChild(meta);
                if (item.url_detalle) {
                    const a = document.createElement('a');
                    a.href = item.url_detalle;
                    a.className = 'hw-chat-card-link';
                    a.textContent = 'Ver detalle';
                    card.appendChild(a);
                }
                cards.appendChild(card);
            });
            block.appendChild(cards);
            parent.appendChild(block);
        }

        function renderOrdersUi(parent, ui) {
            const orders = ui.orders || [];
            if (!orders.length) {
                const empty = document.createElement('p');
                empty.className = 'hw-chat-empty';
                empty.textContent = 'No hay pedidos para mostrar.';
                parent.appendChild(empty);
                return;
            }
            const block = document.createElement('div');
            block.className = 'hw-chat-ui-block';

            const tableWrap = document.createElement('div');
            tableWrap.className = 'hw-chat-table-wrap';
            const table = document.createElement('table');
            table.className = 'hw-chat-table';
            const thead = document.createElement('thead');
            const headRow = document.createElement('tr');
            ['Pedido', 'Estado', 'Total', 'Fecha'].forEach(function (label) {
                const th = document.createElement('th');
                th.scope = 'col';
                th.textContent = label;
                headRow.appendChild(th);
            });
            thead.appendChild(headRow);
            table.appendChild(thead);
            const tbody = document.createElement('tbody');
            orders.forEach(function (pedido) {
                const tr = document.createElement('tr');
                const tdId = document.createElement('td');
                tdId.textContent = '#' + pedido.id;
                const tdEst = document.createElement('td');
                tdEst.textContent = pedido.estado_etiqueta || pedido.estado || '—';
                const tdTotal = document.createElement('td');
                tdTotal.textContent = formatoClp(pedido.total_clp) + ' CLP';
                const tdFecha = document.createElement('td');
                tdFecha.textContent = (pedido.fecha || '').slice(0, 16).replace('T', ' ');
                tr.appendChild(tdId);
                tr.appendChild(tdEst);
                tr.appendChild(tdTotal);
                tr.appendChild(tdFecha);
                tbody.appendChild(tr);
            });
            table.appendChild(tbody);
            tableWrap.appendChild(table);
            block.appendChild(tableWrap);

            const cards = document.createElement('div');
            cards.className = 'hw-chat-cards';
            orders.forEach(function (pedido) {
                const card = document.createElement('article');
                card.className = 'hw-chat-card';
                const title = document.createElement('p');
                title.className = 'hw-chat-card-title';
                title.textContent = 'Pedido #' + pedido.id;
                const meta = document.createElement('p');
                meta.className = 'hw-chat-card-meta';
                meta.textContent =
                    (pedido.estado_etiqueta || pedido.estado) +
                    ' · ' +
                    formatoClp(pedido.total_clp) +
                    ' CLP';
                card.appendChild(title);
                card.appendChild(meta);
                cards.appendChild(card);
            });
            block.appendChild(cards);

            if (ui.orders_url) {
                const link = document.createElement('a');
                link.href = ui.orders_url;
                link.className = 'hw-chat-card-link';
                link.textContent = 'Ver todos mis pedidos';
                block.appendChild(link);
            }
            parent.appendChild(block);
        }

        function introTextForUi(data) {
            const ui = data.ui;
            const reply = data.reply || '';
            if (!ui || !ui.kind) {
                return reply;
            }
            if (ui.kind === 'products' && ui.products && ui.products.length) {
                const firstLine = reply.split('\n')[0];
                if (firstLine && firstLine.length < 160) {
                    return firstLine;
                }
                return 'Resultados del catálogo:';
            }
            if (ui.kind === 'orders') {
                return reply.split('\n')[0] || 'Tus pedidos:';
            }
            if (ui.kind === 'products_empty') {
                return reply;
            }
            return reply;
        }

        function appendBotMessage(data, options) {
            const isError = options && options.error;
            const skipPersist = options && options.skipPersist;
            const bubble = document.createElement('div');
            bubble.className =
                'hw-chat-bubble hw-chat-bubble--bot' + (isError ? ' hw-chat-bubble--error' : '');
            bubble.setAttribute('role', 'article');

            const text = introTextForUi(data);
            if (text) {
                linkifySafe(bubble, text);
            }

            const ui = data.ui;
            if (ui) {
                if (ui.kind === 'products' && ui.products) {
                    renderProductsUi(bubble, ui.products);
                } else if (ui.kind === 'orders') {
                    renderOrdersUi(bubble, ui);
                } else if (ui.kind === 'products_empty') {
                    const empty = document.createElement('p');
                    empty.className = 'hw-chat-empty';
                    empty.textContent = 'Sin coincidencias en el catálogo.';
                    bubble.appendChild(empty);
                }
                maybeAutoExpandForUi(ui);
            } else if (data.reply && !text) {
                linkifySafe(bubble, data.reply);
            }

            messagesEl.appendChild(bubble);
            scrollMessagesToEnd();
            pushHistory('assistant', data.reply || text || '');
            if (!skipPersist) {
                const entry = {
                    role: 'assistant',
                    content: data.reply || text || '',
                    responseType: data.response_type || '',
                };
                if (ui && ui.kind === 'products' && ui.products && sessionApi) {
                    entry.productComponentes = sessionApi.componentesFromProducts(ui.products);
                }
                if (entry.responseType === 'order_status' || entry.responseType === 'order_login') {
                    delete entry.productComponentes;
                }
                displayLog.push(entry);
                persistSession({});
            }
        }

        function setLoading(loading) {
            root.classList.toggle('is-loading', loading);
            sendBtn.disabled = loading;
            input.disabled = loading;
            const loadingEl = root.querySelector('.hw-chat-loading');
            if (loadingEl) {
                loadingEl.setAttribute('aria-hidden', loading ? 'false' : 'true');
            }
        }

        function builderComponentesActuales() {
            if (window.HW_BUILDER_SYNC && typeof window.HW_BUILDER_SYNC.getComponentes === 'function') {
                const piezas = window.HW_BUILDER_SYNC.getComponentes();
                if (Array.isArray(piezas) && piezas.length > 0) {
                    return piezas;
                }
            }
            return null;
        }

        function manejarRespuestaArmado(data) {
            if (data.armado_context && typeof data.armado_context === 'object') {
                buildContext = data.armado_context;
                persistSession({ buildContext: buildContext });
            }
            if (data.proposal_pending) {
                if (sessionApi) {
                    sessionApi.setProposalPending(data.proposal_pending, userKey);
                }
                document.dispatchEvent(
                    new CustomEvent('hw-armado-pending', { detail: data.proposal_pending })
                );
            }
            if (data.applied_build && Array.isArray(data.applied_build.componentes)) {
                document.dispatchEvent(
                    new CustomEvent('hw-armado-apply', { detail: data.applied_build })
                );
                if (window.HW_BUILDER_SYNC && typeof window.HW_BUILDER_SYNC.refresh === 'function') {
                    window.HW_BUILDER_SYNC.refresh();
                }
            }
            if (data.pending_build_action) {
                appendBotMessage({
                    reply: 'Cuando quieras aplicar el cambio, responde: sí, confirmar.',
                });
            }
        }

        async function sendMessage(text) {
            const trimmed = text.trim();
            if (!trimmed || !apiUrl) {
                return;
            }
            appendUserMessage(trimmed);
            input.value = '';
            resetInputHeight();
            setLoading(true);
            try {
                const payload = {
                    message: trimmed,
                    history: history.slice(-10),
                    build_context: buildContext,
                };
                const builderPiezas = builderComponentesActuales();
                if (builderPiezas) {
                    payload.builder_componentes = builderPiezas;
                }
                const response = await fetch(apiUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken'),
                    },
                    credentials: 'same-origin',
                    body: JSON.stringify(payload),
                });
                const data = await response.json().catch(function () {
                    return {};
                });
                if (!response.ok) {
                    throw new Error(data.error || 'No se pudo obtener respuesta.');
                }
                appendBotMessage(data);
                manejarRespuestaArmado(data);
            } catch (err) {
                appendBotMessage(
                    {
                        reply:
                            'Hubo un problema al conectar con el servidor. Intenta de nuevo en unos segundos.',
                    },
                    { error: true }
                );
                console.error('Chat error:', err);
            } finally {
                setLoading(false);
                input.focus();
            }
        }

        function initResize() {
            if (!resizeHandle || !panel) {
                return;
            }
            let dragging = false;
            let startX = 0;
            let startY = 0;
            let startW = 0;
            let startH = 0;

            function onMove(clientX, clientY) {
                const dx = startX - clientX;
                const dy = startY - clientY;
                const maxW = Math.min(window.innerWidth - 24, 720);
                const maxH = window.innerHeight - 48;
                const w = Math.max(280, Math.min(maxW, startW + dx));
                const h = Math.max(320, Math.min(maxH, startH + dy));
                panel.style.width = w + 'px';
                panel.style.height = h + 'px';
                root.classList.remove('hw-chat-size--compact', 'hw-chat-size--expanded');
            }

            function endDrag() {
                dragging = false;
                document.removeEventListener('mousemove', onMouseMove);
                document.removeEventListener('mouseup', endDrag);
            }

            function onMouseMove(e) {
                if (!dragging) {
                    return;
                }
                onMove(e.clientX, e.clientY);
            }

            resizeHandle.addEventListener('mousedown', function (e) {
                if (root.classList.contains('hw-chat-size--fullscreen')) {
                    return;
                }
                e.preventDefault();
                dragging = true;
                startX = e.clientX;
                startY = e.clientY;
                startW = panel.getBoundingClientRect().width;
                startH = panel.getBoundingClientRect().height;
                document.addEventListener('mousemove', onMouseMove);
                document.addEventListener('mouseup', endDrag);
            });

            resizeHandle.addEventListener('keydown', function (e) {
                if (e.key !== 'ArrowUp' && e.key !== 'ArrowDown' && e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') {
                    return;
                }
                e.preventDefault();
                const rect = panel.getBoundingClientRect();
                startW = rect.width;
                startH = rect.height;
                const step = e.shiftKey ? 40 : 20;
                if (e.key === 'ArrowLeft') {
                    onMove(0, 0);
                    panel.style.width = Math.max(280, startW + step) + 'px';
                }
                if (e.key === 'ArrowRight') {
                    panel.style.width = Math.max(280, startW - step) + 'px';
                }
                if (e.key === 'ArrowUp') {
                    panel.style.height = Math.max(320, startH + step) + 'px';
                }
                if (e.key === 'ArrowDown') {
                    panel.style.height = Math.max(320, startH - step) + 'px';
                }
            });
        }

        restorePanelSize();
        initResize();

        sizeButtons.forEach(function (btn) {
            btn.addEventListener('click', function () {
                const size = btn.getAttribute('data-size') || 'compact';
                panel.style.width = '';
                panel.style.height = '';
                setPanelSize(size);
            });
        });

        launcher.addEventListener('click', function () {
            setOpen(!root.classList.contains('is-open'));
        });

        closeBtn.addEventListener('click', function () {
            setOpen(false);
        });

        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && root.classList.contains('is-open')) {
                if (root.classList.contains('hw-chat-size--fullscreen')) {
                    setPanelSize('compact');
                } else {
                    setOpen(false);
                }
            }
        });

        form.addEventListener('submit', function (e) {
            e.preventDefault();
            sendMessage(input.value);
        });

        input.addEventListener('input', autoResizeInput);
        input.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                form.requestSubmit();
            }
        });

        input.addEventListener('focus', function () {
            if (sessionApi) {
                sessionApi.touch(userKey);
            }
        });

        document.addEventListener('hw-builder-state', function (event) {
            const detalle = event.detail || {};
            if (!Array.isArray(detalle.componentes)) {
                return;
            }
            buildContext = Object.assign({}, buildContext || {}, { componentes: detalle.componentes });
            persistSession({ buildContext: buildContext });
        });

        async function restoreDisplayLog() {
            if (!displayLog.length) {
                restoringSession = false;
                if (sessionState && sessionState.open) {
                    setOpen(true);
                }
                return;
            }
            for (let i = 0; i < displayLog.length; i += 1) {
                const entry = displayLog[i];
                if (entry.role === 'user') {
                    appendUserMessage(entry.content, { skipPersist: true });
                } else if (entry.productComponentes && entry.productComponentes.length) {
                    const refreshed = await fetchProductosRevalidados(entry.productComponentes);
                    if (refreshed && refreshed.productos) {
                        appendBotMessage(
                            {
                                reply: entry.content,
                                ui: { kind: 'products', products: refreshed.productos },
                            },
                            { skipPersist: true }
                        );
                        if (refreshed.build_context) {
                            buildContext = refreshed.build_context;
                        }
                    } else {
                        appendBotMessage({ reply: entry.content }, { skipPersist: true });
                    }
                } else {
                    appendBotMessage({ reply: entry.content, response_type: entry.responseType }, {
                        skipPersist: true,
                    });
                }
            }
            restoringSession = false;
            if (sessionState && sessionState.open) {
                setOpen(true);
            }
            persistSession({});
        }

        restoreDisplayLog();

        window.addEventListener('pageshow', function (event) {
            if (event.persisted && sessionApi) {
                sessionApi.load(userKey);
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
