(function(global, utils, rental, productsSection, personnelSection, summaryPanel) {
    if (!rental || !productsSection || !personnelSection || !summaryPanel || !utils) {
        return;
    }

    const API_URL = '/orders/api/calculate-order-total/';
    const resetBtn = document.getElementById('resetOrderBtn');
    const customerNameInput = document.getElementById('customerName');
    const customerPhoneInput = document.getElementById('customerPhone');
    const initiateOrderBtn = document.getElementById('initiateOrderBtn');

    const updateLoadingPayout = (totalAmount = 0) => {
        const allocations = personnelSection.getAllocations();
        const leaderShare = allocations.length ? allocations[0].percentage : 0;
        summaryPanel.updateLoadingPayoutDisplay(allocations, leaderShare, totalAmount);
    };

    const calculateTotals = () => {
        const items = productsSection.getItems();
        const period = rental.getPeriod();

        if (!items.length) {
            summaryPanel.reset();
            updateLoadingPayout(0);
            return;
        }

        const payload = {
            items,
            days: period.days,
            start_date: period.start,
            expected_return_date: period.end,
            prepayment_amount: summaryPanel.getPrepaymentAmount(),
            collateral_amount: summaryPanel.getCollateralAmount()
        };

        fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': utils.getCookie('csrftoken')
            },
            body: JSON.stringify(payload)
        })
            .then(response => response.json())
            .then(data => {
                if (data.success === false || data.error) {
                    throw new Error(data.error || 'Calculation error');
                }
                summaryPanel.applyServerTotals(data);
                updateLoadingPayout(Number(data.total) || 0);
            })
            .catch(err => {
                console.error('Order total calculation failed', err);
                summaryPanel.reset();
                updateLoadingPayout(0);
            });
    };

    const handleReset = () => {
        rental.reset();
        productsSection.reset();
        personnelSection.reset();
        summaryPanel.reset();
        calculateTotals();
    };

    const validateInitiateOrder = () => {
        const missing = [];
        if (!customerNameInput?.value.trim()) {
            missing.push('customer name');
        }
        if (!customerPhoneInput?.value.trim()) {
            missing.push('customer phone');
        }
        if (!productsSection.getItems().length) {
            missing.push('at least one product');
        }
        return missing;
    };

    const handleInitiateOrder = event => {
        event?.preventDefault();
        const missing = validateInitiateOrder();
        if (missing.length) {
            window.alert(`Please provide: ${missing.join(', ')} before initiating the order.`);
            return;
        }
        const period = rental.getPeriod();
        const total = summaryPanel.getLatestTotal();
        const prepayment = summaryPanel.getPrepaymentAmount();
        const collateral = summaryPanel.getCollateralAmount();
        const remaining = Math.max(0, total - prepayment);
        const customerName = customerNameInput?.value.trim() || 'Customer';
        const message = [
            `Order ready for ${customerName}`,
            `Rental duration: ${period.days} day(s)`,
            `Estimated total: ${utils.formatCurrency(total)}`,
            `Prepayment: ${utils.formatCurrency(prepayment)}`,
            `Collateral: ${utils.formatCurrency(collateral)}`,
            `Remaining balance: ${utils.formatCurrency(remaining)}`
        ].join('\\n');
        window.alert(message);
    };

    const init = () => {
        productsSection.init({
            containerId: 'productsContainer',
            onChange: calculateTotals
        });
        personnelSection.init({
            containerId: 'personnelContainer',
            onChange: () => {
                calculateTotals();
                updateLoadingPayout(summaryPanel.getLatestTotal());
            }
        });
        summaryPanel.init({
            prepaymentInputSelector: '#prepaymentAmountInput',
            prepaymentAmountSelector: '#prepaymentAmount',
            prepaymentPercentLabelSelector: '#prepaymentPercentLabel',
            prepaymentPercentDisplaySelector: '#prepaymentPercentDisplay',
            remainingSelector: '#remainingAmount',
            loadingPayoutSelector: '#loadingPersonnelPayoutValue',
            loadingDetailsSelector: '#loadingPersonnelPayoutDetails',
            collateralToggleSelector: '#collateralToggle',
            collateralFieldsSelector: '#collateralFields',
            collateralValueSelector: '#collateralValueInput',
            costBreakdownListSelector: '#costBreakdownList',
            costBreakdownEmptySelector: '#costBreakdownEmpty',
            penaltyInfoSelector: '#penaltyInfo',
            penaltyAmountSelector: '#penaltyAmount',
            penaltyDaysSelector: '#penaltyDays',
            rentalDaysSelector: '#rentalDays',
            estimatedTotalSelector: '#estimatedTotal',
            collateralSummarySelector: '#costBreakdownCollateral',
            collateralSummaryAmountSelector: '#collateralSummaryAmount',
            collateralSummaryTextSelector: '#collateralSummaryText',
            personnelSummarySelector: '#costBreakdownPersonnel',
            personnelSummaryAmountSelector: '#costBreakdownPersonnelAmount',
            personnelSummaryTextSelector: '#costBreakdownPersonnelText',
            clientPaymentSelector: '#costBreakdownClientPayment',
            clientPaymentAmountSelector: '#costBreakdownClientAmount',
            clientPaymentDetailsSelector: '#costBreakdownClientDetails',
            footerCollateralAmountSelector: '#footerCollateralAmount',
            footerCollateralPercentSelector: '#footerCollateralPercent'

        });
        summaryPanel.onPrepaymentChange(calculateTotals);
        summaryPanel.onCollateralChange(() => {
            calculateTotals();
        });

        rental.subscribe(() => {
            if (!productsSection.isReady()) {
                return;
            }
            productsSection.applyGlobalDates();
            calculateTotals();
        });

        rental.init();

        calculateTotals();

        if (resetBtn) {
            resetBtn.addEventListener('click', event => {
                event.preventDefault();
                handleReset();
            });
        }
        if (initiateOrderBtn) {
            initiateOrderBtn.addEventListener('click', handleInitiateOrder);
        }
    };

    document.addEventListener('DOMContentLoaded', init);
})(window, window.OrderUtils, window.OrderRentalPeriod, window.OrderProductsSection, window.OrderPersonnelSection, window.OrderSummaryPanel);
