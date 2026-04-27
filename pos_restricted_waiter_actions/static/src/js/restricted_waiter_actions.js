/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { Orderline, PosStore } from "@point_of_sale/app/store/models";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";

function currentEmployee(pos) {
    return pos.get_cashier ? pos.get_cashier() : pos.cashier || null;
}

function permission(employee, fieldName, defaultValue = false) {
    if (!employee) {
        return defaultValue;
    }
    return employee[fieldName] ?? defaultValue;
}

function showDenied(env, message) {
    env.services.dialog.add(AlertDialog, {
        title: _t("Action Not Allowed"),
        body: message,
    });
}

async function logAttempt(pos, payload) {
    const employee = currentEmployee(pos);
    const order = pos.get_order ? pos.get_order() : null;
    const table = order && order.table ? order.table.name : "";
    const body = {
        employee_id: employee?.id || false,
        user_id: pos.user?.id || false,
        session_id: pos.pos_session?.id || false,
        config_id: pos.config?.id || false,
        order_ref: order?.name || order?.uid || "",
        table_name: table || "",
        ...payload,
    };
    try {
        await fetch('/pos_restricted_waiter_actions/log', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
            credentials: 'same-origin',
        });
    } catch (_error) {
        // Silent by design: logging must never break POS flow.
    }
}

function parsePosNumber(value, fallback = 0) {
    const number = Number(value);
    return Number.isFinite(number) ? number : fallback;
}

function getLineCurrentQuantity(line) {
    if (!line) {
        return 0;
    }
    if (typeof line.get_quantity === q(function)) {
        return parsePosNumber(line.get_quantity(), 0);
    }
    if (line.quantity !== undefined) {
        return parsePosNumber(line.quantity, 0);
    }
    if (line.qty !== undefined) {
        return parsePosNumber(line.qty, 0);
    }
    return 0;
}

function getKitchenSentQty(line) {
    const qtySent = parsePosNumber(line && line.qty_sent, 0);
    if (qtySent > 0) {
        return qtySent;
    }
    if (line && (line.sent_to_kitchen || line.is_from_sync)) {
        return getLineCurrentQuantity(line);
    }
    return 0;
}

function refreshBodyClasses(pos) {
    const employee = currentEmployee(pos);
    const root = document.body;
    if (!root) {
        return;
    }
    root.classList.toggle('o_pos_restricted_hide_backspace', !permission(employee, 'pos_show_backspace', true));
    root.classList.toggle('o_pos_restricted_hide_pay', !permission(employee, 'pos_allow_payment', true));
}

patch(PosStore.prototype, {
    async after_load_server_data(...args) {
        const result = await super.after_load_server_data(...args);
        refreshBodyClasses(this);
        return result;
    },

    set_cashier(employee) {
        const result = super.set_cashier(...arguments);
        refreshBodyClasses(this);
        return result;
    },
});

patch(Orderline.prototype, {
    async set_quantity(quantity, keepPrice) {
        const pos = this.pos;
        const employee = currentEmployee(pos);
        const oldQty = getLineCurrentQuantity(this);
        const newQty = parsePosNumber(quantity, 0);
        const isDecrease = newQty < oldQty;
        const isDelete = newQty <= 0;
        const sentQty = getKitchenSentQty(this);
        const touchesSentQuantity = sentQty > 0 && newQty < sentQty;

        if (touchesSentQuantity && isDecrease && !isDelete && !permission(employee, 'pos_allow_sent_line_decrease', false)) {
            await logAttempt(pos, {
                state: 'denied',
                action: 'decrease_sent_qty',
                product_id: this.product?.id || false,
                product_name: this.product?.display_name || this.product?.name || '',
                line_uuid: this.uuid || '',
                old_qty: oldQty,
                new_qty: newQty,
                sent_qty: sentQty,
                note: 'Decrease below the kitchen-sent quantity was denied by employee permission.',
            });
            showDenied(this.env, _t('You are not allowed to decrease the quantity of lines already sent to the kitchen.'));
            return;
        }

        if (touchesSentQuantity && isDelete && !permission(employee, 'pos_allow_sent_line_delete', false)) {
            await logAttempt(pos, {
                state: 'denied',
                action: 'delete_sent_line',
                product_id: this.product?.id || false,
                product_name: this.product?.display_name || this.product?.name || '',
                line_uuid: this.uuid || '',
                old_qty: oldQty,
                new_qty: 0,
                sent_qty: sentQty,
                note: 'Deletion of a line with kitchen-sent quantity was denied by employee permission.',
            });
            showDenied(this.env, _t('You are not allowed to delete lines already sent to the kitchen.'));
            return;
        }

        if (touchesSentQuantity && isDecrease && !isDelete && permission(employee, 'pos_allow_sent_line_decrease', false)) {
            await logAttempt(pos, {
                state: 'allowed',
                action: 'decrease_sent_qty',
                product_id: this.product?.id || false,
                product_name: this.product?.display_name || this.product?.name || '',
                line_uuid: this.uuid || '',
                old_qty: oldQty,
                new_qty: newQty,
                sent_qty: sentQty,
                note: 'Decrease below the kitchen-sent quantity was allowed.',
            });
        }

        if (touchesSentQuantity && isDelete && permission(employee, 'pos_allow_sent_line_delete', false)) {
            await logAttempt(pos, {
                state: 'allowed',
                action: 'delete_sent_line',
                product_id: this.product?.id || false,
                product_name: this.product?.display_name || this.product?.name || '',
                line_uuid: this.uuid || '',
                old_qty: oldQty,
                new_qty: 0,
                sent_qty: sentQty,
                note: 'Deletion of a line with kitchen-sent quantity was allowed.',
            });
        }

        return await super.set_quantity(quantity, keepPrice);
    },
});

patch(ProductScreen.prototype, {
    async pay() {
        const employee = currentEmployee(this.pos);
        if (!permission(employee, 'pos_allow_payment', true)) {
            await logAttempt(this.pos, {
                state: 'denied',
                action: 'open_payment',
                note: 'Opening the payment screen was denied by employee permission.',
            });
            showDenied(this, _t('You are not allowed to open the payment screen.'));
            return;
        }
        await logAttempt(this.pos, {
            state: 'allowed',
            action: 'open_payment',
            note: 'Opening the payment screen was allowed.',
        });
        return await super.pay(...arguments);
    },

    async onNumpadClick(buttonValue) {
        const employee = currentEmployee(this.pos);
        const isBackspace = buttonValue === 'Backspace' || buttonValue === '⌫' || buttonValue === 'backspace';
        if (isBackspace && !permission(employee, 'pos_show_backspace', true)) {
            await logAttempt(this.pos, {
                state: 'denied',
                action: 'backspace',
                note: 'Backspace usage was denied by employee permission.',
            });
            showDenied(this, _t('You are not allowed to use the backspace control.'));
            return;
        }
        return await super.onNumpadClick(...arguments);
    },

    async _deleteOrder() {
        const employee = currentEmployee(this.pos);
        if (!permission(employee, 'pos_allow_order_delete', false)) {
            await logAttempt(this.pos, {
                state: 'denied',
                action: 'delete_order',
                note: 'Deleting the entire order was denied by employee permission.',
            });
            showDenied(this, _t('You are not allowed to delete the entire order.'));
            return;
        }
        await logAttempt(this.pos, {
            state: 'allowed',
            action: 'delete_order',
            note: 'Deleting the entire order was allowed.',
        });
        return await super._deleteOrder(...arguments);
    },
});

patch(PaymentScreen.prototype, {
    async validateOrder(isForceValidate) {
        const employee = currentEmployee(this.pos);
        if (!permission(employee, 'pos_allow_payment', true)) {
            await logAttempt(this.pos, {
                state: 'denied',
                action: 'validate_payment',
                note: 'Payment validation was denied by employee permission.',
            });
            showDenied(this, _t('You are not allowed to validate payment.'));
            return;
        }
        await logAttempt(this.pos, {
            state: 'allowed',
            action: 'validate_payment',
            note: 'Payment validation was allowed.',
        });
        return await super.validateOrder(...arguments);
    },
});
