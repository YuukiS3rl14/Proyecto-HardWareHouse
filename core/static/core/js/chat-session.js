/**
 * Persistencia de sesión del chat (sessionStorage, TTL por inactividad).
 * No almacena pedidos, credenciales ni datos privados de cuenta.
 */
(function (global) {
    'use strict';

    var STORAGE_KEY = 'hw_chat_session';
    var TTL_MS = 10 * 60 * 1000;
    var LEGACY_KEYS = ['hw_chat_panel_size', 'hw_armado_pending'];

    function now() {
        return Date.now();
    }

    function emptyState(userKey) {
        return {
            v: 1,
            userKey: userKey || 'anon',
            lastActivity: now(),
            open: false,
            panelSize: 'compact',
            history: [],
            displayLog: [],
            buildContext: null,
            proposalPending: null,
        };
    }

    function readRaw() {
        try {
            var raw = sessionStorage.getItem(STORAGE_KEY);
            if (!raw) {
                return null;
            }
            return JSON.parse(raw);
        } catch (e) {
            return null;
        }
    }

    function writeRaw(state) {
        try {
            sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
        } catch (e) {
            console.warn('HWChatSession: no se pudo guardar', e);
        }
    }

    function isExpired(state) {
        if (!state || !state.lastActivity) {
            return true;
        }
        return now() - state.lastActivity > TTL_MS;
    }

    function migrateLegacy(state, userKey) {
        try {
            var size = sessionStorage.getItem('hw_chat_panel_size');
            if (size && (size === 'compact' || size === 'expanded' || size === 'fullscreen')) {
                state.panelSize = size;
                sessionStorage.removeItem('hw_chat_panel_size');
            }
            var legacyProp = localStorage.getItem('hw_armado_pending');
            if (legacyProp && !state.proposalPending) {
                state.proposalPending = JSON.parse(legacyProp);
                localStorage.removeItem('hw_armado_pending');
            }
        } catch (e) {
            /* ignore */
        }
        state.userKey = userKey;
        return state;
    }

    function sanitizeDisplayEntry(entry) {
        if (!entry || !entry.role || !entry.content) {
            return null;
        }
        var out = {
            role: entry.role === 'user' ? 'user' : 'assistant',
            content: String(entry.content).slice(0, 4000),
        };
        if (entry.responseType) {
            out.responseType = String(entry.responseType).slice(0, 40);
        }
        if (entry.productComponentes && Array.isArray(entry.productComponentes)) {
            out.productComponentes = entry.productComponentes.slice(0, 24);
        }
        if (entry.role === 'assistant' && entry.responseType === 'order_status') {
            return { role: 'assistant', content: out.content, responseType: out.responseType };
        }
        return out;
    }

    function sanitizeHistory(history) {
        if (!Array.isArray(history)) {
            return [];
        }
        var out = [];
        history.forEach(function (item) {
            if (!item || !item.role || !item.content) {
                return;
            }
            if (item.role !== 'user' && item.role !== 'assistant') {
                return;
            }
            out.push({ role: item.role, content: String(item.content).slice(0, 2000) });
        });
        return out.slice(-20);
    }

    function sanitizeBuildContext(ctx) {
        if (!ctx || typeof ctx !== 'object') {
            return null;
        }
        var limpio = {};
        var campos = [
            'presupuesto_clp',
            'presupuesto_original_clp',
            'snapshot',
            'proposito',
            'preferencia_cpu',
            'indice_economico',
            'total_clp',
            'componentes',
            'pending_action',
            'ultimo_intent',
        ];
        campos.forEach(function (key) {
            if (ctx[key] !== undefined && ctx[key] !== null) {
                limpio[key] = ctx[key];
            }
        });
        if (limpio.pedidos) {
            delete limpio.pedidos;
        }
        return Object.keys(limpio).length ? limpio : null;
    }

    var HWChatSession = {
        TTL_MS: TTL_MS,

        load: function (userKey) {
            var key = userKey || 'anon';
            var state = readRaw();
            if (!state || isExpired(state)) {
                state = emptyState(key);
                migrateLegacy(state, key);
                writeRaw(state);
                return state;
            }
            if (state.userKey !== key) {
                HWChatSession.clear();
                state = emptyState(key);
                migrateLegacy(state, key);
                writeRaw(state);
                return state;
            }
            state.history = sanitizeHistory(state.history);
            state.displayLog = (state.displayLog || [])
                .map(sanitizeDisplayEntry)
                .filter(Boolean)
                .slice(-30);
            state.buildContext = sanitizeBuildContext(state.buildContext);
            return state;
        },

        save: function (partial, userKey) {
            var key = userKey || 'anon';
            var state = HWChatSession.load(key);
            if (partial.open !== undefined) {
                state.open = !!partial.open;
            }
            if (partial.panelSize) {
                state.panelSize = partial.panelSize;
            }
            if (partial.history) {
                state.history = sanitizeHistory(partial.history);
            }
            if (partial.displayLog) {
                state.displayLog = partial.displayLog
                    .map(sanitizeDisplayEntry)
                    .filter(Boolean)
                    .slice(-30);
            }
            if (partial.buildContext !== undefined) {
                state.buildContext = sanitizeBuildContext(partial.buildContext);
            }
            if (partial.proposalPending !== undefined) {
                state.proposalPending = partial.proposalPending;
            }
            state.userKey = key;
            state.lastActivity = now();
            writeRaw(state);
            return state;
        },

        touch: function (userKey) {
            return HWChatSession.save({}, userKey);
        },

        clear: function () {
            try {
                sessionStorage.removeItem(STORAGE_KEY);
            } catch (e) {
                /* ignore */
            }
            LEGACY_KEYS.forEach(function (k) {
                try {
                    sessionStorage.removeItem(k);
                    localStorage.removeItem(k);
                } catch (e2) {
                    /* ignore */
                }
            });
        },

        getProposalPending: function (userKey) {
            var state = HWChatSession.load(userKey);
            return state.proposalPending;
        },

        setProposalPending: function (proposal, userKey) {
            HWChatSession.save({ proposalPending: proposal }, userKey);
        },

        bindLogoutForms: function () {
            document.querySelectorAll('.hw-chat-logout-form').forEach(function (form) {
                form.addEventListener('submit', function () {
                    HWChatSession.clear();
                });
            });
        },

        componentesFromProducts: function (products) {
            if (!Array.isArray(products)) {
                return [];
            }
            return products
                .map(function (p) {
                    if (!p || !p.modelo || p.producto_pk == null) {
                        return null;
                    }
                    return { tipo: p.modelo, id: p.producto_pk };
                })
                .filter(Boolean);
        },
    };

    global.HWChatSession = HWChatSession;

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function () {
            HWChatSession.bindLogoutForms();
        });
    } else {
        HWChatSession.bindLogoutForms();
    }
})(window);
