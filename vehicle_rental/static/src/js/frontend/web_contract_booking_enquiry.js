/** @odoo-module **/
import { loadJS } from "@web/core/assets";

$(document).ready(async function () {
    await loadJS('/vehicle_rental/static/src/js/lib/moment.min.js')
    await loadJS('/vehicle_rental/static/src/js/lib/daterangepicker.js')
    var currentDate = moment().format("YYYY-MM-DD");

    function dateRangeFunction(start, end, label) {
        var selectedStartDate = start.format('YYYY-MM-DD HH:mm');
        var selectedEndDate = end.format('YYYY-MM-DD HH:mm');

        if (selectedStartDate === selectedEndDate) {
            selectedEndDate = (moment(selectedEndDate, "YYYY-MM-DD HH:mm").add(1, 'days')).format('YYYY-MM-DD HH:mm')
        }

        let checkinInput = $('#start_date');
        let checkoutInput = $('#end_date');

        checkinInput.val(selectedStartDate);
        checkoutInput.val(selectedEndDate);

        var checkOutPicker = checkoutInput.data('daterangepicker');
        checkOutPicker.setStartDate(selectedStartDate);
        checkOutPicker.setEndDate(selectedEndDate);

        var checkInPicker = checkinInput.data('daterangepicker');
        checkInPicker.setStartDate(selectedStartDate);
        checkInPicker.setEndDate(selectedEndDate);

        // Update the auto-detected price type badge on the search form
        updatePriceTypeBadge(selectedStartDate, selectedEndDate);
    }

    /**
     * Determine price type based on the duration between two datetime strings.
     * Mirrors the server-side get_auto_price_type() logic.
     *
     * Rules:
     *   < 24 hours              → hour
     *   24 hrs to < 7 days      → day
     *   7 days to < 28 days     → week
     *   28 days to < 365 days   → month
     *   >= 365 days             → year
     */
    function getAutoPriceType(startStr, endStr) {
        if (!startStr || !endStr) return null;
        var start = moment(startStr, 'YYYY-MM-DD HH:mm');
        var end = moment(endStr, 'YYYY-MM-DD HH:mm');
        if (!start.isValid() || !end.isValid()) return null;

        var totalHours = end.diff(start, 'hours', true);
        if (totalHours < 24) return 'hour';
        var totalDays = totalHours / 24;
        if (totalDays < 7) return 'day';
        if (totalDays < 28) return 'week';
        if (totalDays < 365) return 'month';
        return 'year';
    }

    var priceTypeLabels = {
        'hour': 'Hourly Rate',
        'day': 'Daily Rate',
        'week': 'Weekly Rate',
        'month': 'Monthly Rate',
        'year': 'Yearly Rate',
    };

    function updatePriceTypeBadge(startStr, endStr) {
        var pt = getAutoPriceType(startStr, endStr);
        var badge = $('#auto-price-type-badge');
        if (pt && badge.length) {
            badge.text('Pricing: ' + (priceTypeLabels[pt] || pt)).removeClass('d-none');
        }
    }

    if ($('#start_date').val() && $('#end_date').val()) {
        $('#start_date, #end_date').daterangepicker({
            locale: { format: 'YYYY-MM-DD HH:mm' },
            timePicker: true,
            timePicker24Hour: true,
            timePickerIncrement: 1,
            "alwaysShowCalendars": true,
            "minDate": currentDate,
            "startDate": $('#start_date').val(),
            "endDate": $('#end_date').val(),
            autoApply: true,
            autoUpdateInput: false,
        }, function (start, end, label) {
            dateRangeFunction(start, end, label)
        });
        // Show badge on page load if dates already set
        updatePriceTypeBadge($('#start_date').val(), $('#end_date').val());
    } else {
        $('#start_date, #end_date').daterangepicker({
            locale: { format: 'YYYY-MM-DD HH:mm' },
            timePicker: true,
            timePicker24Hour: true,
            timePickerIncrement: 1,
            "alwaysShowCalendars": true,
            "minDate": currentDate,
            autoApply: true,
            autoUpdateInput: false,
        }, function (start, end, label) {
            dateRangeFunction(start, end, label)
        });
    }

    function validateVehicleSearch() {
        let isValid = true;
        $('.error-message').remove();

        const startDateInput = $('#start_date');
        const endDateInput = $('#end_date');

        const now = new Date();

        const startDate = startDateInput.val() ? new Date(startDateInput.val()) : null;
        const endDate = endDateInput.val() ? new Date(endDateInput.val()) : null;

        // Validate Start Date
        if (!startDateInput.val()) {
            $('.search-card').after('<div class="error-message text-danger mt-2">Please select a start date.</div>');
            isValid = false;
        } else if (startDate < now) {
            $('.search-card').after('<div class="error-message text-danger mt-2">Start date and time cannot be in the past.</div>');
            isValid = false;
        }

        // Validate End Date
        if (!endDateInput.val()) {
            $('.search-card').after('<div class="error-message text-danger mt-2">Please select an end date.</div>');
            isValid = false;
        } else if (endDate < now) {
            $('.search-card').after('<div class="error-message text-danger mt-2">End date and time cannot be in the past.</div>');
            isValid = false;
        } else if (startDate && endDate <= startDate) {
            $('.search-card').after('<div class="error-message text-danger mt-2">End date and time must be greater than start date.</div>');
            isValid = false;
        }

        // Note: No price type validation needed — it is auto-detected from dates

        return isValid;
    }

    // Attach validation on form submit
    const form = $('form[action="/get/available/vehicles"]');
    if (form.length) {
        form.on('submit', function (e) {
            if (!validateVehicleSearch()) {
                e.preventDefault();
            }
        });
    }

    // ── Vehicle list filter handlers ──────────────────────────────────────────

    $('#vehicle_filter_category_id').on('change', function () {
        let CategoryId = $(this).val();
        if (!CategoryId) {
            const urlParams = new URLSearchParams(window.location.search);
            urlParams.delete('vehicle_category_id');
            const newParam = urlParams.toString();
            window.location.href = window.location.pathname + (newParam ? '?' + newParam : '');
            return;
        }
        const urlParams = new URLSearchParams(window.location.search);
        urlParams.set('vehicle_category_id', CategoryId);
        window.location.href = window.location.pathname + '?' + urlParams.toString();
    });

    $('#priceFilter').on('change', function () {
        let price = $(this).val();
        if (!price) {
            const urlParams = new URLSearchParams(window.location.search);
            urlParams.delete('price');
            const newParam = urlParams.toString();
            window.location.href = window.location.pathname + (newParam ? '?' + newParam : '');
            return;
        }
        const urlParams = new URLSearchParams(window.location.search);
        urlParams.set('price', price);
        window.location.href = window.location.pathname + '?' + urlParams.toString();
    });

    $('#transmissionFilter').on('change', function () {
        let transmission_type = $(this).val();
        if (!transmission_type) {
            const urlParams = new URLSearchParams(window.location.search);
            urlParams.delete('tr');
            const newParam = urlParams.toString();
            window.location.href = window.location.pathname + (newParam ? '?' + newParam : '');
            return;
        }
        const urlParams = new URLSearchParams(window.location.search);
        urlParams.set('tr', transmission_type);
        window.location.href = window.location.pathname + '?' + urlParams.toString();
    });

    $('#fuelFilter').on('change', function () {
        let fuel_type = $(this).val();
        if (!fuel_type) {
            const urlParams = new URLSearchParams(window.location.search);
            urlParams.delete('ft');
            const newParam = urlParams.toString();
            window.location.href = window.location.pathname + (newParam ? '?' + newParam : '');
            return;
        }
        const urlParams = new URLSearchParams(window.location.search);
        urlParams.set('ft', fuel_type);
        window.location.href = window.location.pathname + '?' + urlParams.toString();
    });

    $('#seatsFilter').on('change', function () {
        let seats = $(this).val();
        if (!seats) {
            const urlParams = new URLSearchParams(window.location.search);
            urlParams.delete('seats');
            const newParam = urlParams.toString();
            window.location.href = window.location.pathname + (newParam ? '?' + newParam : '');
            return;
        }
        const urlParams = new URLSearchParams(window.location.search);
        urlParams.set('seats', seats);
        window.location.href = window.location.pathname + '?' + urlParams.toString();
    });

    // ── Booking form validation ───────────────────────────────────────────────

    function validateBookingEnquiry() {
        let isValid = true;
        $('.error-message').remove();

        const contactNameInput = $('input[name="contact_name"]');
        const phoneInput = $('input[name="phone"]');
        const emailInput = $('input[name="email_from"]');
        const termsCheckbox = $('#termsAccepted');

        // Validate Name
        if (!contactNameInput.val() || contactNameInput.val().trim() === '') {
            contactNameInput.after('<div class="error-message text-danger">Please enter your name.</div>');
            isValid = false;
        }

        // Validate Phone
        if (!phoneInput.val() || phoneInput.val().trim() === '') {
            phoneInput.after('<div class="error-message text-danger">Please enter your phone number.</div>');
            isValid = false;
        } else if (!/^[\d\s\-\(\)\+]+$/.test(phoneInput.val())) {
            phoneInput.after('<div class="error-message text-danger">Please enter a valid phone number.</div>');
            isValid = false;
        }

        // Validate Email
        if (!emailInput.val() || emailInput.val().trim() === '') {
            emailInput.after('<div class="error-message text-danger">Please enter your email address.</div>');
            isValid = false;
        } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailInput.val())) {
            emailInput.after('<div class="error-message text-danger">Please enter a valid email address.</div>');
            isValid = false;
        }

        // Validate Terms and Conditions
        if (!termsCheckbox.is(':checked')) {
            termsCheckbox.closest('.form-check').after('<div class="error-message text-danger">You must accept the Terms and Conditions and Privacy Policy.</div>');
            isValid = false;
        }

        return isValid;
    }

    const bookingForm = $('form[action="/rental/booking-enquiry"]');
    if (bookingForm.length) {
        bookingForm.on('submit', function (e) {
            if (!validateBookingEnquiry()) {
                e.preventDefault();
            }
        });
    }

});