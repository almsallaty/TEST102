(function () {
    'use strict';

    const DIGIT_MAP = {
        '٠': '0',
        '١': '1',
        '٢': '2',
        '٣': '3',
        '٤': '4',
        '٥': '5',
        '٦': '6',
        '٧': '7',
        '٨': '8',
        '٩': '9',
    };

    const ARABIC_DIGITS_RE = /[٠-٩]/g;
    const HAS_ARABIC_DIGITS_RE = /[٠-٩]/;

    function toLatinDigits(value) {
        if (typeof value !== 'string' || !HAS_ARABIC_DIGITS_RE.test(value)) {
            return value;
        }
        return value.replace(ARABIC_DIGITS_RE, function (d) {
            return DIGIT_MAP[d] || d;
        });
    }

    function convertElement(el) {
        if (!el || el.nodeType !== 1) {
            return;
        }

        if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
            if (el.value) {
                const newValue = toLatinDigits(el.value);
                if (newValue !== el.value) {
                    el.value = newValue;
                }
            }
            if (el.placeholder) {
                const newPlaceholder = toLatinDigits(el.placeholder);
                if (newPlaceholder !== el.placeholder) {
                    el.placeholder = newPlaceholder;
                }
            }
            return;
        }

        if (el.children.length === 0 && el.textContent) {
            const newText = toLatinDigits(el.textContent);
            if (newText !== el.textContent) {
                el.textContent = newText;
            }
        }
    }

    function scan(root) {
        if (!root) {
            return;
        }

        convertElement(root);

        const elements = root.querySelectorAll(
            '.o_form_view input,' +
            '.o_form_view textarea,' +
            '.o_form_view span,' +
            '.o_form_view div,' +
            '.o_list_view td,' +
            '.modal input,' +
            '.modal textarea,' +
            '.modal span,' +
            '.modal div'
        );

        for (let i = 0; i < elements.length; i++) {
            convertElement(elements[i]);
        }
    }

    let scheduled = false;

    function scheduleScan() {
        if (scheduled) {
            return;
        }
        scheduled = true;
        window.requestAnimationFrame(function () {
            scheduled = false;
            scan(document.body);
        });
    }

    document.addEventListener('DOMContentLoaded', scheduleScan);
    window.addEventListener('load', scheduleScan);
    document.addEventListener('input', scheduleScan, true);
    document.addEventListener('change', scheduleScan, true);
    document.addEventListener('click', function () {
        setTimeout(scheduleScan, 50);
    }, true);

    const observer = new MutationObserver(function (mutations) {
        for (let i = 0; i < mutations.length; i++) {
            if (mutations[i].addedNodes && mutations[i].addedNodes.length) {
                scheduleScan();
                return;
            }
        }
    });

    function startObserver() {
        if (document.body) {
            observer.observe(document.body, {
                childList: true,
                subtree: true,
            });
            scheduleScan();
        }
    }

    if (document.body) {
        startObserver();
    } else {
        document.addEventListener('DOMContentLoaded', startObserver);
    }
})();
