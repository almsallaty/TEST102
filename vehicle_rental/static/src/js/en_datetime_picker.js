/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, xml, useRef, onMounted, onPatched, onWillUnmount } from "@odoo/owl";
import { DateTime } from "luxon";

function valueToLuxon(value) {
    if (!value) {
        return null;
    }
    if (DateTime.isDateTime && DateTime.isDateTime(value)) {
        return value;
    }
    if (typeof value === "string") {
        let dt = DateTime.fromISO(value);
        if (!dt.isValid) {
            dt = DateTime.fromSQL(value);
        }
        return dt.isValid ? dt : null;
    }
    if (value.ts) {
        try {
            const dt = DateTime.fromObject(value);
            if (dt.isValid) {
                return dt;
            }
        } catch (_e) {
        }
    }
    if (value instanceof Date) {
        return DateTime.fromJSDate(value);
    }
    return null;
}

function valueToMoment(value) {
    const dt = valueToLuxon(value);
    if (!dt || !window.moment) {
        return null;
    }
    return window.moment(dt.toJSDate());
}

function formatDisplay(value) {
    const dt = valueToLuxon(value);
    if (!dt) {
        return "";
    }
    return dt.setLocale("en").toFormat("dd-MM-yyyy hh:mm a").toUpperCase();
}

export class EnDateTimePickerField extends Component {
    static template = xml`
        <t t-if="props.readonly">
            <span class="o_field_en_datetime" t-esc="displayValue"/>
        </t>
        <input t-else="" t-ref="input" type="text" class="o_input" readonly="readonly" t-att-value="displayValue"/>
    `;
    static props = {
        ...standardFieldProps,
    };
    static supportedTypes = ["datetime"];

    setup() {
        this.inputRef = useRef("input");
        onMounted(() => this._syncPicker());
        onPatched(() => this._syncPicker());
        onWillUnmount(() => this._destroyPicker());
    }

    get displayValue() {
        return formatDisplay(this.props.value);
    }

    _destroyPicker() {
        const input = this.inputRef.el;
        if (!input || !window.jQuery) {
            return;
        }
        const $input = window.jQuery(input);
        const picker = $input.data("daterangepicker");
        if (picker) {
            picker.remove();
        }
    }

    _syncPicker() {
        const input = this.inputRef.el;
        if (!input || this.props.readonly || !window.jQuery || !window.moment) {
            return;
        }
        const $input = window.jQuery(input);
        let picker = $input.data("daterangepicker");
        const currentMoment = valueToMoment(this.props.value) || window.moment();

        if (!picker) {
            $input.daterangepicker({
                singleDatePicker: true,
                timePicker: true,
                timePicker24Hour: false,
                autoUpdateInput: true,
                locale: {
                    format: "DD-MM-YYYY hh:mm A",
                    applyLabel: "Apply",
                    cancelLabel: "Clear",
                    direction: "ltr",
                },
                startDate: currentMoment,
            });
            picker = $input.data("daterangepicker");
            $input.on("apply.daterangepicker", (_ev, drp) => {
                const jsDate = drp.startDate.toDate();
                const dt = DateTime.fromJSDate(jsDate);
                this.props.update(dt);
                input.value = drp.startDate.format("DD-MM-YYYY hh:mm A");
            });
        }

        if (picker) {
            picker.setStartDate(currentMoment);
            picker.setEndDate(currentMoment);
            input.value = currentMoment.format("DD-MM-YYYY hh:mm A");
        }
    }
}

registry.category("fields").add("en_datetime_picker", EnDateTimePickerField);
