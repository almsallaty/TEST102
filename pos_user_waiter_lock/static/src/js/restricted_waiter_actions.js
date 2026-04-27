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
const EPSILON = 0.000001;

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
    return pos?.get_order?.() || pos?.getOrder?.() || pos?.selectedOrder || null;
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
    if (Array.isArray(order.lines)) {
        return order.lines;
    }
    if (Array.isArray(order.orderlines)) {
        return order.orderlines;
    }
    if (typeof order.getOrderlines === "function") {
        return order.getOrderlines() || [];
    }
    if (typeof order.get_orderlines === "function") {
        return order.get_orderlines() || [];
    }
    return [];
}

function getLineIdentifier(line) {
    if (!line) {
        return null;
    }
    return line.preparationKey || line.uuid || line.uid || line.cid || line.id || line.line_uuid || line.server_id || null;
}

function getLineQty(line) {
    const value = line?.getQuantity
        ? line.getQuantity()
        : line?.get_quantity
          ? line.get_quantity()
          : line?.qty ?? line?.quantity ?? 0;
    const qty = Number(value);
    return Number.isFinite(qty) ? qty : 0;
}

function getPreparationLines(order) {
    const change = order?.last_order_preparation_change;
    if (!change || typeof change !== "object") {
        return {};
    }
    const lines = change.lines || {};
    return lines && typeof lines === "object" ? lines : {};
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

function parseStoredMap(value) {
    if (!value) {
        return {};
    }
    try {
        const parsed = JSON.parse(value);
        return parsed && typeof parsed === "object" ? parsed : {};
    } catch {
        return {};
    }
}

function loadSentQtyMap(order) {
    if (!order) {
        return {};
    }
    let map = order._waiterLockSentQtyByLine;
    if (!map || typeof map !== "object") {
        map = {};
    }

    const identifier = getOrderIdentifier(order);
    if (identifier) {
        try {
            map = {
                ...parseStoredMap(window.localStorage.getItem(`${SENT_QTY_PREFIX}${identifier}`)),
                ...map,
            };
        } catch {
            // ignore local storage errors
        }
    }

    order._waiterLockSentQtyByLine = map;
    return map;
}

function saveSentQtyMap(order, map) {
    if (!order) {
        return;
    }
    order._waiterLockSentQtyByLine = map && typeof map === "object" ? map : {};
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

function buildSentQtyMapFromPreparation(order) {
    const map = {};
    const lines = getPreparationLines(order);
    for (const [key, value] of Object.entries(lines)) {
        if (!value || typeof value !== "object") {
            continue;
        }
        const qty = Number(value.quantity ?? value.qty ?? 0);
        if (!Number.isFinite(qty) || Math.abs(qty) <= EPSILON) {
            continue;
        }
        for (const lineKey of [key, value.uuid, value.line_uuid, value.preparationKey].filter(Boolean)) {
            map[lineKey] = qty;
        }
    }
    return map;
}

function ensureSentQtyMap(order) {
    const existingMap = loadSentQtyMap(order);
    if (Object.keys(existingMap).length || !hasPreparationChange(order)) {
        return existingMap;
    }
    const map = buildSentQtyMapFromPreparation(order);
    saveSentQtyMap(order, map);
    return map;
}

function markOrderSent(order) {
    if (!order) {
        return;
    }
    order._waiterLockSent = true;

    const map = {};
    for (const line of getOrderLines(order)) {
        const lineId = getLineIdentifier(line);
        if (!lineId) {
            continue;
        }
        const qty = getLineQty(line);
        if (Math.abs(qty) > EPSILON) {
            map[lineId] = qty;
        }
    }

    const preparationMap = buildSentQtyMapFromPreparation(order);
    saveSentQtyMap(order, { ...map, ...preparationMap });

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
    const map = ensureSentQtyMap(order);
    const qty = Number(map[lineId] ?? 0);
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
            const previousDate = order.last_order_preparation_change?.metadata?.serverDate || "";
            setTimeout(() => {
                const nextDate = order.last_order_preparation_change?.metadata?.serverDate || "";
                if (nextDate && nextDate !== previousDate) {
                    markOrderSent(order);
                }
            }, 700);
        },
        true
    );
}

function shouldBlockDecrease(line, quantity) {
    if (!STATE.loaded || !STATE.blockQuantityDecrease || !line) {
        return false;
    }
    const order = line.order_id || line.order || line.pos?.get_order?.() || line.pos?.getOrder?.();
    const sentQty = getSentQtyForLine(order, line);
    if (Math.abs(sentQty) <= EPSILON) {
        return false;
    }
    if (quantity === "" || quantity === null || quantity === undefined) {
        return true;
    }
    const nextQty = Number(quantity);
    if (!Number.isFinite(nextQty)) {
        return false;
    }
    return nextQty < sentQty - EPSILON;
}

function shouldBlockRemoveLine(order, line) {
    if (!STATE.loaded || !STATE.blockLineRemove || !order || !line) {
        return false;
    }
    const lines = typeof line.getAllLinesInCombo === "function" ? line.getAllLinesInCombo() : [line];
    return lines.some((lineToCheck) => Math.abs(getSentQtyForLine(order, lineToCheck)) > EPSILON);
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
        this._waiterLockSentQtyByLine = this._waiterLockSentQtyByLine || {};
        if (hasPreparationChange(this)) {
            this._waiterLockSent = true;
            ensureSentQtyMap(this);
        }
    },

    updateLastOrderChange() {
        const result = super.updateLastOrderChange(...arguments);
        markOrderSent(this);
        return result;
    },

    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        json._waiterLockSent = !!this._waiterLockSent || hasPreparationChange(this);
        json._waiterLockSentQtyByLine = this._waiterLockSentQtyByLine || {};
        return json;
    },

    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        this._waiterLockSent = !!json?._waiterLockSent || hasPreparationChange(this);
        this._waiterLockSentQtyByLine = json?._waiterLockSentQtyByLine || this._waiterLockSentQtyByLine || {};
        if (hasPreparationChange(this)) {
            ensureSentQtyMap(this);
        }
    },

    removeOrderline(line) {
        if (shouldBlockRemoveLine(this, line)) {
            warn(_t("You cannot remove a line that was already sent to preparation. You can remove newly added unsent lines."));
            return false;
        }
        return super.removeOrderline(...arguments);
    },
});

patch(PosOrderline.prototype, {
    setQuantity(quantity, keepPrice) {
        if (shouldBlockDecrease(this, quantity)) {
            warn(_t("You cannot decrease sent quantities below the last kitchen-sent quantity. New unsent additions can still be removed before sending again."));
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
