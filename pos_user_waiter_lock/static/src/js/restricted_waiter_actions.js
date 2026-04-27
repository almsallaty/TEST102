/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { onWillStart } from "@odoo/owl";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { PosOrderline } from "@point_of_sale/app/models/pos_order_line";
import { PosStore } from "@point_of_sale/app/services/pos_store";
import { Numpad } from "@point_of_sale/app/components/numpad/numpad";

const STATE = {
    loaded: false,
    blockQuantityDecrease: false,
    blockLineRemove: false,
    blockPayment: false,
    blockCancelOrder: false,
    hideKeypad: false,
    loadingPromise: null,
    sendListenerAttached: false,
};

const STORAGE_PREFIX = "pos_user_waiter_lock_sent_";
const SENT_QTY_PREFIX = "pos_user_waiter_lock_sent_qty_";

function jsonRpc(url, params) {
    return fetch(url, {
        method: "POST",
        credentials: "same-origin",
        headers: {
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest",
        },
        body: JSON.stringify({
            jsonrpc: "2.0",
            method: "call",
            params,
            id: Date.now(),
        }),
    })
        .then((r) => r.json())
        .then((payload) => {
            if (payload.error) {
                const message = payload.error?.data?.message || payload.error?.message || _t("Unknown RPC error");
                throw new Error(message);
            }
            return payload.result;
        });
}

async function loadSettings() {
    const settings = await jsonRpc("/web/dataset/call_kw", {
        model: "pos.user.waiter.lock.service",
        method: "get_current_permissions",
        args: [],
        kwargs: {},
    });

    STATE.blockQuantityDecrease = !!settings?.block_quantity_decrease;
    STATE.blockLineRemove = !!settings?.block_line_remove;
    STATE.blockPayment = !!settings?.block_payment;
    STATE.blockCancelOrder = !!settings?.block_cancel_order;
    STATE.hideKeypad = !!settings?.hide_keypad;
    STATE.loaded = true;
    applyBackspaceVisibility();
}

function ensureSettingsLoaded() {
    if (STATE.loaded) {
        return Promise.resolve();
    }
    if (STATE.loadingPromise) {
        return STATE.loadingPromise;
    }
    STATE.loadingPromise = loadSettings()
        .catch(() => {
            STATE.loaded = true;
        })
        .finally(() => {
            STATE.loadingPromise = null;
            applyBackspaceVisibility();
        });
    return STATE.loadingPromise;
}

function warn(message) {
    window.alert(message);
}

function shouldHideBackspace() {
    return STATE.loaded && STATE.hideKeypad;
}

function applyBackspaceVisibility() {
    document.body.classList.toggle("pos-restricted-hide-backspace", shouldHideBackspace());
}

function getPosStore() {
    return window.odoo?.__WOWL_DEBUG__?.root?.env?.services?.pos || null;
}

function getCurrentOrder() {
    const pos = getPosStore();
    return pos?.get_order?.() || null;
}

function getOrderIdentifier(order) {
    if (!order) {
        return null;
    }
    return order.uuid || order.uid || order.cid || order.name || order.sequence_number || null;
}

function getOrderLines(order) {
    if (!order) {
        return [];
    }
    if (typeof order.get_orderlines === "function") {
        return order.get_orderlines() || [];
    }
    const lines = order.lines || order.orderlines || [];
    if (Array.isArray(lines)) {
        return lines;
    }
    if (Array.isArray(lines.models)) {
        return lines.models;
    }
    if (Array.isArray(lines.records)) {
        return lines.records;
    }
    if (typeof lines === "object") {
        return Object.values(lines);
    }
    return [];
}

function getLineIdentifier(line) {
    if (!line) {
        return null;
    }
    return line.uuid || line.uid || line.cid || line.id || line.line_uuid || line.server_id || null;
}

function getLineQty(line) {
    const qty = Number(line?.get_quantity ? line.get_quantity() : line?.qty ?? line?.quantity ?? 0);
    return Number.isFinite(qty) ? qty : 0;
}

function loadSentQtyMap(order) {
    if (!order) {
        return {};
    }
    if (order._waiterLockSentQtyByLine && typeof order._waiterLockSentQtyByLine === "object") {
        return order._waiterLockSentQtyByLine;
    }
    const identifier = getOrderIdentifier(order);
    if (!identifier) {
        order._waiterLockSentQtyByLine = {};
        return order._waiterLockSentQtyByLine;
    }
    try {
        const raw = window.localStorage.getItem(`${SENT_QTY_PREFIX}${identifier}`);
        order._waiterLockSentQtyByLine = raw ? JSON.parse(raw) || {} : {};
    } catch {
        order._waiterLockSentQtyByLine = {};
    }
    return order._waiterLockSentQtyByLine;
}

function saveSentQtyMap(order, map) {
    if (!order) {
        return;
    }
    order._waiterLockSentQtyByLine = map || {};
    const identifier = getOrderIdentifier(order);
    if (!identifier) {
        return;
    }
    try {
        window.localStorage.setItem(`${SENT_QTY_PREFIX}${identifier}`, JSON.stringify(order._waiterLockSentQtyByLine));
    } catch {
        // ignore local storage errors
    }
}

function markOrderSent(order) {
    if (!order) {
        return;
    }
    order._waiterLockSent = true;

    const sentQtyByLine = { ...loadSentQtyMap(order) };
    for (const line of getOrderLines(order)) {
        const lineId = getLineIdentifier(line);
        if (!lineId) {
            continue;
        }
        const qty = getLineQty(line);
        if (qty > 0) {
            sentQtyByLine[lineId] = qty;
        } else {
            delete sentQtyByLine[lineId];
        }
    }
    saveSentQtyMap(order, sentQtyByLine);

    const identifier = getOrderIdentifier(order);
    if (identifier) {
        try {
            window.localStorage.setItem(`${STORAGE_PREFIX}${identifier}`, "1");
        } catch {
            // ignore local storage errors
        }
    }
}

function isOrderMarkedSent(order) {
    if (!order) {
        return false;
    }
    if (order._waiterLockSent) {
        return true;
    }
    const identifier = getOrderIdentifier(order);
    if (!identifier) {
        return false;
    }
    try {
        return window.localStorage.getItem(`${STORAGE_PREFIX}${identifier}`) === "1";
    } catch {
        return false;
    }
}

function hasPreparationChange(order) {
    if (!order) {
        return false;
    }
    const change = order.last_order_preparation_change;
    if (!change || typeof change !== "object") {
        return false;
    }
    const metadata = change.metadata || {};
    const lines = change.lines || {};
    return !!(metadata.serverDate || Object.keys(lines).length);
}

function orderWasAlreadySent(order) {
    return isOrderMarkedSent(order) || hasPreparationChange(order);
}

function getSentQtyForLine(order, line) {
    if (!order || !line || !orderWasAlreadySent(order)) {
        return 0;
    }
    const lineId = getLineIdentifier(line);
    if (!lineId) {
        return 0;
    }
    const sentQtyByLine = loadSentQtyMap(order);
    const qty = Number(sentQtyByLine[lineId] || 0);
    return Number.isFinite(qty) ? qty : 0;
}

function attachSendButtonListener() {
    if (STATE.sendListenerAttached) {
        return;
    }
    STATE.sendListenerAttached = true;
    document.addEventListener(
        "click",
        (event) => {
            const target = event.target instanceof Element ? event.target : null;
            const button = target?.closest("button, .btn, .button, .control-button, .input-button");
            if (!button) {
                return;
            }
            const text = (button.textContent || "").replace(/\s+/g, " ").trim().toLowerCase();
            if (!text.startsWith("send")) {
                return;
            }
            const order = getCurrentOrder();
            if (!order) {
                return;
            }
            setTimeout(() => markOrderSent(order), 0);
        },
        true
    );
}

function shouldBlockDecrease(line, quantity) {
    if (!STATE.loaded || !STATE.blockQuantityDecrease || !line) {
        return false;
    }
    const order = line.order || line.order_id || line.pos?.get_order?.();
    const sentQty = getSentQtyForLine(order, line);
    if (sentQty <= 0) {
        return false;
    }
    if (quantity === "" || quantity === null || quantity === undefined) {
        return sentQty > 0;
    }
    const nextQty = Number(quantity);
    if (!Number.isFinite(nextQty)) {
        return false;
    }
    return nextQty < sentQty;
}

patch(ProductScreen.prototype, {
    async setup() {
        await super.setup(...arguments);
        attachSendButtonListener();
        ensureSettingsLoaded();
    },

    async pay() {
        await ensureSettingsLoaded();
        if (STATE.blockPayment) {
            warn(_t("You are not allowed to open the payment screen on this POS."));
            return false;
        }
        return await super.pay(...arguments);
    },
});

patch(PaymentScreen.prototype, {
    async validateOrder() {
        await ensureSettingsLoaded();
        if (STATE.blockPayment) {
            warn(_t("You are not allowed to make payment on this POS."));
            return false;
        }
        return await super.validateOrder(...arguments);
    },
});

patch(PosStore.prototype, {
    async beforeDeleteOrder(order, options = {}) {
        await ensureSettingsLoaded();
        if (STATE.blockCancelOrder && orderWasAlreadySent(order)) {
            warn(_t("You are not allowed to delete a table or order after it was sent to preparation."));
            return false;
        }
        return await super.beforeDeleteOrder(order, options);
    },
});

patch(PosOrder.prototype, {
    setup() {
        super.setup(...arguments);
        this._waiterLockSent = this._waiterLockSent || false;
        if (hasPreparationChange(this)) {
            this._waiterLockSent = true;
        }
    },

    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        json._waiterLockSent = !!this._waiterLockSent || hasPreparationChange(this);
        json._waiterLockSentQtyByLine = loadSentQtyMap(this);
        return json;
    },

    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        this._waiterLockSent = !!json?._waiterLockSent || hasPreparationChange(this);
        this._waiterLockSentQtyByLine = json?._waiterLockSentQtyByLine || {};
    },

    removeOrderline(line) {
        if (line && STATE.loaded && STATE.blockLineRemove && getSentQtyForLine(this, line) > 0) {
            warn(_t("You cannot remove a line that was already sent to preparation. You can remove newly added unsent lines."));
            return false;
        }
        return super.removeOrderline(...arguments);
    },
});

patch(PosOrderline.prototype, {
    setQuantity(quantity, keepPrice) {
        if (shouldBlockDecrease(this, quantity)) {
            warn(_t("You cannot decrease quantities after this order was sent to preparation. You can only add items."));
            return false;
        }
        return super.setQuantity(quantity, keepPrice);
    },
});

patch(Numpad.prototype, {
    setup() {
        super.setup(...arguments);
        this._hideRestrictedBackspace = false;

        onWillStart(async () => {
            await ensureSettingsLoaded();
            this._hideRestrictedBackspace = shouldHideBackspace();
            applyBackspaceVisibility();
        });

        const originalOnClick = this.onClick;
        this.onClick = (buttonValue) => {
            this._hideRestrictedBackspace = shouldHideBackspace();
            if (this._hideRestrictedBackspace && buttonValue === "Backspace") {
                return;
            }
            return originalOnClick(buttonValue);
        };
    },

    get buttons() {
        const buttons = super.buttons || [];
        this._hideRestrictedBackspace = shouldHideBackspace();
        applyBackspaceVisibility();
        if (!this._hideRestrictedBackspace) {
            return buttons;
        }
        return buttons.filter((button) => {
            const value = typeof button === "object" ? button.value : button;
            return value !== "Backspace";
        });
    },
});
