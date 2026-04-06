(function(global, utils) {
    const state = {
        startEl: null,
        returnEl: null,
        displayEl: null,
        rentalDaysEl: null,
        listeners: [],
        defaults: {
            start: null,
            return: null
        }
    };

    const labelForDays = days => `Rental Duration: ${days} day${days === 1 ? '' : 's'}`;

    const notify = () => {
        const listenerPayload = getPeriod();
        state.listeners.forEach(listener => {
            try {
                listener(listenerPayload);
            } catch (err) {
                console.error('Rental period listener error', err);
            }
        });
    };

    const updateDisplay = () => {
        if (!state.startEl || !state.returnEl) {
            return;
        }
        const startValue = state.startEl.value;
        const returnValue = state.returnEl.value;
        const days = utils.calculateDays(startValue, returnValue);

        if (state.displayEl) {
            state.displayEl.textContent = labelForDays(days);
        }

        if (state.rentalDaysEl) {
            state.rentalDaysEl.textContent = days;
        }

        notify();
    };

    const getPeriod = () => ({
        start: state.startEl?.value || '',
        end: state.returnEl?.value || '',
        days: utils.calculateDays(state.startEl?.value, state.returnEl?.value)
    });

    const handleChange = () => {
        updateDisplay();
    };

    const reset = () => {
        if (state.startEl && state.defaults.start) {
            state.startEl.value = state.defaults.start;
        }
        if (state.returnEl && state.defaults.return) {
            state.returnEl.value = state.defaults.return;
        }
        updateDisplay();
    };

    const init = options => {
        const {
            startSelector = '#startDate',
            returnSelector = '#returnDate',
            displaySelector = '#rentalDaysDisplay',
            rentalDaysSelector = '#rentalDays'
        } = options || {};

        state.startEl = document.querySelector(startSelector);
        state.returnEl = document.querySelector(returnSelector);
        state.displayEl = document.querySelector(displaySelector);
        state.rentalDaysEl = document.querySelector(rentalDaysSelector);

        if (state.startEl) {
            state.defaults.start = state.startEl.dataset.default || state.startEl.value || '';
            state.startEl.addEventListener('change', handleChange);
        }

        if (state.returnEl) {
            state.defaults.return = state.returnEl.dataset.default || state.returnEl.value || '';
            state.returnEl.addEventListener('change', handleChange);
        }

        updateDisplay();
    };

    global.OrderRentalPeriod = {
        init,
        subscribe: listener => {
            if (typeof listener === 'function') {
                state.listeners.push(listener);
            }
        },
        getPeriod,
        reset
    };
})(window, window.OrderUtils || (window.OrderUtils = {}));
