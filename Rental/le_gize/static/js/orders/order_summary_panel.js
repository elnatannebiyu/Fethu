(function(global, utils) {
    const state = {
        estimatedTotal: 0,
        prepaymentInput: null,
        prepaymentAmountLabel: null,
        prepaymentPercentLabel: null,
        prepaymentPercentDisplay: null,
        remainingLabel: null,
        prepaymentEditing: false,
        loadingValueEl: null,
        loadingDetailsEl: null,
        collateralToggle: null,
        collateralFields: null,
        collateralInput: null,
        collateralSummaryContainer: null,
        collateralSummaryAmount: null,
        collateralSummaryText: null,
        collateralOverride: false,
        collateralChangeCallback: null,
        collateralPercent: 0,
        costBreakdownList: null,
        costBreakdownEmpty: null,
        personnelSummaryContainer: null,
        personnelSummaryAmount: null,
        personnelSummaryText: null,
        clientPaymentContainer: null,
        clientPaymentAmount: null,
        clientPaymentDetails: null,
        footerCollateralAmount: null,
        footerCollateralPercent: null,
        penaltyInfoEl: null,
        penaltyAmountEl: null,
        penaltyDaysEl: null,
        rentalDaysEl: null,
        estimatedTotalEl: null,
        prepaymentChangeCallback: null,
        suppressPercentUpdate: false
    };

    const COMMISSION_POOL_RATE = 0.1;
    const COLLATERAL_RATE = 0.5;

    const extrasMarkup = extras => {
        if (!extras.length) {
            return '';
        }
        return extras.map(extra => {
            const days = Number(extra.days) || 1;
            const pricePerDay = Number(extra.price_per_day) || 0;
            const perDayTotal = pricePerDay * days;
            const oneTimeTotal = Number(extra.one_time_total) || 0;
            const subtotalText = utils.formatCurrency(perDayTotal + oneTimeTotal);
            const perDayDesc = `$${pricePerDay.toFixed(2)}/day × ${days} day(s)`;
            const oneTimeLine = oneTimeTotal > 0
                ? `<p class="text-[0.65rem] text-gray-500 dark:text-gray-400">One-time fee: ${utils.formatCurrency(oneTimeTotal)}</p>`
                : '';
            return `
                <div class="space-y-0.5">
                    <p class="text-[0.65rem] text-gray-500 dark:text-gray-400">
                        ${extra.name} · ${perDayDesc} = ${utils.formatCurrency(perDayTotal)}
                    </p>
                    ${oneTimeLine}
                    <p class="text-[0.65rem] text-gray-400 dark:text-gray-500">
                        Total: ${subtotalText}
                    </p>
                </div>
            `;
        }).join('');
    };

    const renderCostBreakdown = details => {
        if (!state.costBreakdownList || !state.costBreakdownEmpty) {
            return;
        }
        const markup = details.map(item => {
            return `
                <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3 shadow-sm">
                    <div class="flex justify-between text-sm font-semibold text-gray-900 dark:text-white">
                        <span>${item.name}</span>
                        <span>${utils.formatCurrency(item.subtotal)}</span>
                    </div>
                    <p class="text-[0.65rem] text-gray-500 mt-1">
                        ${item.quantity} × ${item.days} day(s) @ $${item.price_per_day}/day
                    </p>
                    <p class="text-[0.65rem] text-gray-500">
                        Rental period: ${item.start_date || '—'} → ${item.expected_return_date || '—'}
                    </p>
                    ${extrasMarkup(item.extras)}
                </div>
            `;
        }).join('');

        const defaultRow = () => `
            <div class="bg-white dark:bg-gray-800 border border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-3 shadow-sm">
                <p class="text-sm font-semibold text-gray-800 dark:text-gray-100">No products yet</p>
                <p class="text-[0.75rem] text-gray-500 dark:text-gray-400 mt-1">Start by adding a product or extra to see what the customer owes.</p>
            </div>
        `;

        const hasDetails = Boolean(details?.length);
        const contentMarkup = hasDetails ? markup : defaultRow();

        state.costBreakdownEmpty.classList.toggle('hidden', hasDetails);
        state.costBreakdownList.innerHTML = contentMarkup;
    };

    const updatePrepaymentPercent = percent => {
        if (state.prepaymentPercentLabel) {
            state.prepaymentPercentLabel.textContent = `${percent.toFixed(2)}%`;
        }
        if (state.prepaymentPercentDisplay) {
            state.prepaymentPercentDisplay.textContent = `${percent.toFixed(2)}%`;
        }
    };

    const getCollateralAmount = () => Number(state.collateralInput?.value) || 0;

    const updateCollateralSummary = () => {
        const container = state.collateralSummaryContainer;
        if (!container || !state.collateralToggle) {
            return;
        }
        const amount = getCollateralAmount();
        if (!state.collateralToggle.checked || amount <= 0) {
            container.classList.add('hidden');
            return;
        }
        container.classList.remove('hidden');
        if (state.collateralSummaryAmount) {
            state.collateralSummaryAmount.textContent = utils.formatCurrency(amount);
        }
        if (state.collateralSummaryText) {
            const ratio = state.collateralPercent || (state.estimatedTotal > 0 ? Math.min(100, (amount / state.estimatedTotal) * 100) : 0);
            const modeText = state.collateralOverride ? 'Manual override' : 'Auto-filled';
        state.collateralSummaryText.textContent = `${modeText} at ${ratio.toFixed(2)}% of the subtotal.`;
        }
    };

    const setCollateralValue = (value, options = {}) => {
        if (!state.collateralInput) {
            return;
        }
        if (!options.force && state.collateralOverride) {
            return;
        }
        state.collateralInput.value = Number(value || 0).toFixed(2);
        updateCollateralSummary();
    };

    const handleCollateralInput = () => {
        if (!state.collateralInput) {
            return;
        }
        state.collateralOverride = true;
        updateCollateralSummary();
        if (typeof state.collateralChangeCallback === 'function') {
            state.collateralChangeCallback();
        }
    };

    const updateCollateralFields = (options = {}) => {
        if (!state.collateralToggle || !state.collateralFields || !state.collateralInput) {
            return;
        }
        if (state.collateralToggle.checked) {
            state.collateralFields.classList.remove('hidden');
            if (!state.collateralOverride) {
                setCollateralValue(0, { force: true });
            }
        } else {
            state.collateralFields.classList.add('hidden');
            setCollateralValue(0, { force: true });
            state.collateralOverride = false;
        }
        if (options.notify && typeof state.collateralChangeCallback === 'function') {
            state.collateralChangeCallback();
        }
    };

    const updatePersonnelSummary = (pool, weight) => {
        const container = state.personnelSummaryContainer;
        if (!container) {
            return;
        }
        if (!pool || weight <= 0) {
            container.classList.add('hidden');
            return;
        }
        container.classList.remove('hidden');
        if (state.personnelSummaryAmount) {
            state.personnelSummaryAmount.textContent = utils.formatCurrency(pool);
        }
        if (state.personnelSummaryText) {
            state.personnelSummaryText.textContent = `Based on ${weight.toFixed(2)} weight`;
        }
    };

    const updateLoadingPayoutDisplay = (allocations = [], leaderShare = 0, totalAmount = 0) => {
        if (!state.loadingValueEl || !state.loadingDetailsEl) {
            updatePersonnelSummary(0, 0);
            return;
        }
        if (!allocations.length || leaderShare <= 0 || totalAmount <= 0) {
            state.loadingValueEl.textContent = '$0.00';
            state.loadingDetailsEl.textContent = 'Select personnel to calculate their share';
            updatePersonnelSummary(0, 0);
            return;
        }
        const pool = totalAmount * COMMISSION_POOL_RATE;
        state.loadingValueEl.textContent = utils.formatCurrency(pool);
        const details = allocations.map(entry => {
            const ratio = leaderShare > 0 ? (entry.percentage / leaderShare) : 0;
            const earned = pool * ratio;
            const name = entry.name || 'Personnel';
            return `<p class="text-xs text-purple-600 dark:text-purple-200">${name} · ${entry.percentage.toFixed(2)}% · ${utils.formatCurrency(earned)}</p>`;
        }).join('');
            state.loadingDetailsEl.innerHTML = details || 'Select personnel to calculate their share';
        updatePersonnelSummary(pool, leaderShare);
    };

    const parsePrepaymentValue = () => {
        if (!state.prepaymentInput) {
            return 0;
        }
        const amount = Number(state.prepaymentInput.value);
        if (Number.isNaN(amount) || amount < 0) {
            return 0;
        }
        return amount;
    };

    const handlePrepaymentInput = () => {
        if (state.suppressPercentUpdate) {
            state.suppressPercentUpdate = false;
            return;
        }
        const amount = parsePrepaymentValue();
        const percent = state.estimatedTotal > 0 ? Math.min(100, Math.max(0, (amount / state.estimatedTotal) * 100)) : 0;
        updatePrepaymentPercent(percent);
        if (typeof state.prepaymentChangeCallback === 'function') {
            state.prepaymentChangeCallback();
        }
    };

    const init = options => {
        state.prepaymentInput = document.querySelector(options?.prepaymentInputSelector || '#prepaymentAmountInput');
        state.prepaymentAmountLabel = document.querySelector(options?.prepaymentAmountSelector || '#prepaymentAmount');
        state.prepaymentPercentLabel = document.querySelector(options?.prepaymentPercentLabelSelector || '#prepaymentPercentLabel');
        state.prepaymentPercentDisplay = document.querySelector(options?.prepaymentPercentDisplaySelector || '#prepaymentPercentDisplay');
        state.remainingLabel = document.querySelector(options?.remainingSelector || '#remainingAmount');
        state.loadingValueEl = document.querySelector(options?.loadingPayoutSelector || '#loadingPersonnelPayoutValue');
        state.loadingDetailsEl = document.querySelector(options?.loadingDetailsSelector || '#loadingPersonnelPayoutDetails');
        state.collateralToggle = document.querySelector(options?.collateralToggleSelector || '#collateralToggle');
        state.collateralFields = document.querySelector(options?.collateralFieldsSelector || '#collateralFields');
        state.collateralInput = document.querySelector(options?.collateralValueSelector || '#collateralValueInput');
        state.costBreakdownList = document.querySelector(options?.costBreakdownListSelector || '#costBreakdownList');
        state.costBreakdownEmpty = document.querySelector(options?.costBreakdownEmptySelector || '#costBreakdownEmpty');
        state.penaltyInfoEl = document.querySelector(options?.penaltyInfoSelector || '#penaltyInfo');
        state.penaltyAmountEl = document.querySelector(options?.penaltyAmountSelector || '#penaltyAmount');
        state.penaltyDaysEl = document.querySelector(options?.penaltyDaysSelector || '#penaltyDays');
        state.rentalDaysEl = document.querySelector(options?.rentalDaysSelector || '#rentalDays');
        state.estimatedTotalEl = document.querySelector(options?.estimatedTotalSelector || '#estimatedTotal');
        state.collateralSummaryContainer = document.querySelector(options?.collateralSummarySelector || '#costBreakdownCollateral');
        state.collateralSummaryAmount = document.querySelector(options?.collateralSummaryAmountSelector || '#collateralSummaryAmount');
        state.collateralSummaryText = document.querySelector(options?.collateralSummaryTextSelector || '#collateralSummaryText');
        state.personnelSummaryContainer = document.querySelector(options?.personnelSummarySelector || '#costBreakdownPersonnel');
        state.personnelSummaryAmount = document.querySelector(options?.personnelSummaryAmountSelector || '#costBreakdownPersonnelAmount');
        state.personnelSummaryText = document.querySelector(options?.personnelSummaryTextSelector || '#costBreakdownPersonnelText');
        state.clientPaymentContainer = document.querySelector(options?.clientPaymentSelector || '#costBreakdownClientPayment');
        state.clientPaymentAmount = document.querySelector(options?.clientPaymentAmountSelector || '#costBreakdownClientAmount');
        state.clientPaymentDetails = document.querySelector(options?.clientPaymentDetailsSelector || '#costBreakdownClientDetails');
        state.footerCollateralAmount = document.querySelector(options?.footerCollateralAmountSelector || '#footerCollateralAmount');
        state.footerCollateralPercent = document.querySelector(options?.footerCollateralPercentSelector || '#footerCollateralPercent');

        state.prepaymentInput?.addEventListener('input', handlePrepaymentInput);
        state.prepaymentInput?.addEventListener('focus', () => {
            state.prepaymentEditing = true;
        });
        state.prepaymentInput?.addEventListener('blur', () => {
            state.prepaymentEditing = false;
            const amount = parsePrepaymentValue();
            state.prepaymentInput.value = amount.toFixed(2);
        });
        state.collateralToggle?.addEventListener('change', () => updateCollateralFields({ notify: true }));
        state.collateralInput?.addEventListener('input', handleCollateralInput);
        updateCollateralFields({ notify: false });
    };

    const updateEstimatedTotalDisplay = total => {
        if (state.estimatedTotalEl) {
            state.estimatedTotalEl.textContent = utils.formatCurrency(total);
        }
    };

        const updateClientPaymentDisplay = (clientPayment, prepayment, remaining, collateral, collateralPercent, prepaymentPercent) => {
            const container = state.clientPaymentContainer;
            if (!container) {
                return;
            }
            if (clientPayment <= 0) {
                container.classList.add('hidden');
                return;
            }
            container.classList.remove('hidden');
            if (state.clientPaymentAmount) {
                state.clientPaymentAmount.textContent = utils.formatCurrency(clientPayment);
            }
            if (state.clientPaymentDetails) {
                state.clientPaymentDetails.innerHTML = `
                    <p>Prepayment (${prepaymentPercent.toFixed(2)}%): ${utils.formatCurrency(prepayment)}</p>
                    <p>Remaining: ${utils.formatCurrency(remaining)}</p>
                    <p>Collateral (${collateralPercent.toFixed(2)}%): ${utils.formatCurrency(collateral)}</p>
                `;
            }
        };

    const setEstimatedTotal = total => {
        state.estimatedTotal = total;
        updateEstimatedTotalDisplay(total);
        updateCollateralFields({ notify: false });
    };

    const applyServerTotals = data => {
        const total = Number(data.total) || 0;
        const prepaymentValue = Number(data.prepayment) || 0;
        const remainingValue = Number(data.remaining) || 0;
        const prepaymentPercentValue = Number(data.prepayment_percent) || 0;
        const penaltyAmount = Number(data.penalty_amount) || 0;
        const penaltyDays = Number(data.penalty_days) || 0;
        const rentalDays = Number(data.rental_days) || 0;

        setEstimatedTotal(total);
        if (state.prepaymentAmountLabel) {
            state.prepaymentAmountLabel.textContent = utils.formatCurrency(prepaymentValue);
        }
        if (state.remainingLabel) {
            state.remainingLabel.textContent = utils.formatCurrency(remainingValue);
        }
        updatePrepaymentPercent(prepaymentPercentValue);
        if (state.prepaymentInput && !state.prepaymentEditing) {
            state.suppressPercentUpdate = true;
            state.prepaymentInput.value = prepaymentValue.toFixed(2);
        }
        renderCostBreakdown(data.details || []);
        updatePenaltyDisplay(penaltyAmount, penaltyDays);
        if (state.rentalDaysEl) {
            state.rentalDaysEl.textContent = rentalDays;
        }
        const collateralAmount = Number(data.collateral_amount) || 0;
        const collateralPercentValue = Number(data.collateral_percent) || 0;
        if (state.footerCollateralAmount) {
            state.footerCollateralAmount.textContent = utils.formatCurrency(collateralAmount);
        }
        if (state.footerCollateralPercent) {
            state.footerCollateralPercent.textContent = `${collateralPercentValue.toFixed(2)}%`;
        }
        const clientPaymentValue = Number(data.client_payment) || 0;
        state.collateralPercent = collateralPercentValue;
        updateCollateralSummary();
        updateClientPaymentDisplay(clientPaymentValue, prepaymentValue, remainingValue, collateralAmount, collateralPercentValue, prepaymentPercentValue);
    };

    const reset = () => {
        setEstimatedTotal(0);
        if (state.prepaymentAmountLabel) {
            state.prepaymentAmountLabel.textContent = '$0.00';
        }
        if (state.remainingLabel) {
            state.remainingLabel.textContent = '$0.00';
        }
        updatePrepaymentPercent(0);
        if (state.prepaymentInput) {
            state.suppressPercentUpdate = true;
            state.prepaymentInput.value = '0.00';
        }
        renderCostBreakdown([]);
        updateLoadingPayoutDisplay(0, 0);
        updatePenaltyDisplay(0, 0);
        if (state.rentalDaysEl) {
            state.rentalDaysEl.textContent = '0';
        }
        state.collateralOverride = false;
        updateCollateralSummary();
        if (state.personnelSummaryContainer) {
            state.personnelSummaryContainer.classList.add('hidden');
        }
        if (state.clientPaymentContainer) {
            state.clientPaymentContainer.classList.add('hidden');
        }
        if (state.collateralSummaryContainer) {
            state.collateralSummaryContainer.classList.add('hidden');
        }
    };

    const getPrepaymentAmount = () => Number(state.prepaymentInput?.value) || 0;

    const getLatestTotal = () => state.estimatedTotal;

    const onPrepaymentChange = callback => {
        state.prepaymentChangeCallback = callback;
    };

    const onCollateralChange = callback => {
        state.collateralChangeCallback = callback;
    };

    function updatePenaltyDisplay(amount, days) {
        if (!state.penaltyInfoEl || !state.penaltyAmountEl || !state.penaltyDaysEl) {
            return;
        }
        if (amount <= 0 || days <= 0) {
            state.penaltyInfoEl.classList.add('hidden');
            return;
        }
        state.penaltyAmountEl.textContent = utils.formatCurrency(amount);
        state.penaltyDaysEl.textContent = days;
        state.penaltyInfoEl.classList.remove('hidden');
    }

    global.OrderSummaryPanel = {
        init,
        setEstimatedTotal,
        applyServerTotals,
        renderCostBreakdown,
        updateLoadingPayoutDisplay,
        reset,
        getPrepaymentAmount,
        getLatestTotal,
        onPrepaymentChange,
        getCollateralAmount,
        onCollateralChange
    };
})(window, window.OrderUtils || (window.OrderUtils = {}));
