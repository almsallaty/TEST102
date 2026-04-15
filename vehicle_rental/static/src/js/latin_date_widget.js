/** @odoo-module **/

import { registry } from "@web/core/registry";
import { DateField } from "@web/views/fields/date/date_field";
import { DateTimeField } from "@web/views/fields/datetime/datetime_field";
import { onMounted, onPatched } from "@odoo/owl";

function toLatinDigits(value) {
    if (typeof value !== "string") {
        return value;
    }
    const map = {
        "٠": "0",
        "١": "1",
        "٢": "2",
        "٣": "3",
        "٤": "4",
        "٥": "5",
        "٦": "6",
        "٧": "7",
        "٨": "8",
        "٩": "9",
    };
    return value.replace(/[٠-٩]/g, (d) => map[d] || d);
}

function patchDigits(root) {
    if (!root) {
        return;
    }

    const nodes = root.querySelectorAll("input, span, div");
    for (const node of nodes) {
        if (node.tagName === "INPUT") {
            if (node.value) {
                const newValue = toLatinDigits(node.value);
                if (newValue !== node.value) {
                    node.value = newValue;
                }
            }
            if (node.placeholder) {
                const newPlaceholder = toLatinDigits(node.placeholder);
                if (newPlaceholder !== node.placeholder) {
                    node.placeholder = newPlaceholder;
                }
            }
            continue;
        }

        if (node.children.length === 0 && node.textContent) {
            const newText = toLatinDigits(node.textContent);
            if (newText !== node.textContent) {
                node.textContent = newText;
            }
        }
    }
}

class LatinDateField extends DateField {
    setup() {
        super.setup();
        const apply = () => patchDigits(this.el);
        onMounted(apply);
        onPatched(apply);
    }
}
LatinDateField.template = DateField.template;
LatinDateField.supportedTypes = ["date"];

class LatinDateTimeField extends DateTimeField {
    setup() {
        super.setup();
        const apply = () => patchDigits(this.el);
        onMounted(apply);
        onPatched(apply);
    }
}
LatinDateTimeField.template = DateTimeField.template;
LatinDateTimeField.supportedTypes = ["datetime"];

registry.category("fields").add("latin_date", LatinDateField);
registry.category("fields").add("latin_datetime", LatinDateTimeField);
