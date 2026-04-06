(function(global, utils, rental) {
    console.log('OrderProductsSection v2 loaded');
    const state = {
        container: null,
        containerId: 'productsContainer',
        templateId: 'productRowTemplate',
        addButtonId: 'addProductBtn',
        subtotalSelectors: ['#productsSectionSubtotal', '#productsTotalAmount'],
        onChange: null
    };

    const getContainer = () => {
        if (state.container) {
            return state.container;
        }
        if (state.containerId) {
            const found = document.getElementById(state.containerId);
            if (found) {
                state.container = found;
                return found;
            }
        }
        return null;
    };

    const MS_PER_DAY = 1000 * 60 * 60 * 24;

    const getNewRow = () => {
        const container = getContainer();
        if (!container) {
            return null;
        }
        const template = document.getElementById(state.templateId);
        if (!template) {
            return null;
        }
        const clone = template.content.cloneNode(true);
        container.appendChild(clone);
        return container.querySelector('.product-row:last-child');
    };

    const getRowElements = row => {
        let extrasContainer = row.querySelector('.extras-container');
        let extrasList = row.querySelector('.extras-list');
        if (!extrasList) {
            extrasList = document.createElement('div');
            extrasList.className = 'extras-list grid gap-2';
            if (extrasContainer) {
                extrasContainer.appendChild(extrasList);
            } else {
                row.appendChild(extrasList);
            }
        }
        const extrasNote = row.querySelector('.extras-note');
        return {
            select: row.querySelector('.product-select'),
            quantity: row.querySelector('.product-quantity'),
            extrasList,
            extrasContainer,
            extrasPreview: row.querySelector('[data-extras-preview]'),
            extrasNote,
            start: row.querySelector('.product-start-date'),
            end: row.querySelector('.product-return-date'),
            daysDisplay: row.querySelector('.product-days-display strong'),
            totalLabel: row.querySelector('.product-total-amount'),
            stockStatus: row.querySelector('.product-stock-status')
        };
    };

    const calculateRowDays = row => {
        const { start, end } = getRowElements(row);
        const startValue = start?.value || rental.getPeriod().start;
        const endValue = end?.value || rental.getPeriod().end;
        return utils.calculateDays(startValue, endValue);
    };

    const formatExtrasOption = (extra) => {
        const parts = [`$${extra.price_per_day}/day`];
        if (extra.one_time_fee && Number(extra.one_time_fee) > 0) {
            parts.push(`+$${Number(extra.one_time_fee).toFixed(2)} one-time`);
        }
        return `${extra.name} - ${parts.join(' ')}`;
    };

    const renderLineTotal = (row, amount) => {
        const { totalLabel } = getRowElements(row);
        if (totalLabel) {
            totalLabel.textContent = utils.formatCurrency(amount);
        }
    };

    const calculateRowTotal = row => {
        const { select, quantity, extrasList } = getRowElements(row);
        if (!select?.value) {
            return 0;
        }
        const pricePerDay = Number(select.selectedOptions[0]?.dataset?.price) || 0;
        const qty = Math.max(1, Number(quantity?.value) || 1);
        const days = calculateRowDays(row);
        const baseTotal = pricePerDay * qty * days;

        const extrasOptions = Array.from(extrasList?.querySelectorAll('.extra-checkbox:checked') || []);
        const extrasPerDay = extrasOptions.reduce((sum, checkbox) => {
            return sum + (Number(checkbox.dataset?.price) || 0) * qty * days;
        }, 0);
        const extrasOneTime = extrasOptions.reduce((sum, checkbox) => {
            return sum + (Number(checkbox.dataset?.oneTime) || 0) * qty;
        }, 0);

        return baseTotal + extrasPerDay + extrasOneTime;
    };

    const updateSelectedProducts = () => {
        const container = getContainer();
        if (!container) {
            return;
        }
        const selectedIds = Array.from(container.querySelectorAll('.product-select'))
            .map(select => select.value)
            .filter(Boolean);

        container.querySelectorAll('.product-select').forEach(select => {
            Array.from(select.options).forEach(option => {
                if (!option.value) {
                    option.disabled = false;
                    return;
                }
                if (option.value === select.value) {
                    option.disabled = false;
                    return;
                }
                option.disabled = selectedIds.includes(option.value);
            });
        });
    };

    const updateRowDuration = row => {
        const days = calculateRowDays(row);
        const { daysDisplay } = getRowElements(row);
        if (daysDisplay) {
            daysDisplay.textContent = days;
        }
        renderLineTotal(row, calculateRowTotal(row));
        return days;
    };

    const addRow = () => {
        const row = getNewRow();
        if (!row) {
            return;
        }
        row.dataset.syncGlobal = 'true';
        const { select, quantity, start, end } = getRowElements(row);

        const markCustomDates = () => {
            if (row.dataset.syncGlobal === 'true') {
                row.dataset.syncGlobal = 'false';
            }
        };

        const refresh = () => {
            if (select.value) {
                updateRowDuration(row);
                triggerChange();
            }
        };

        select?.addEventListener('change', () => {
            loadExtras(row);
            checkStock(row);
            refresh();
            updateSelectedProducts();
        });

        quantity?.addEventListener('input', refresh);

        [start, end].forEach(input => {
            input?.addEventListener('change', () => {
                markCustomDates();
                refresh();
            });
        });

        row.querySelector('.remove-product')?.addEventListener('click', () => {
            removeRow(row);
        });

        if (start) {
            start.value = rental.getPeriod().start;
        }
        if (end) {
            end.value = rental.getPeriod().end;
        }

        updateRowDuration(row);
        updateSelectedProducts();

        gsap.from(row, {
            opacity: 0,
            x: -20,
            duration: 0.3,
            ease: 'power2.out'
        });
    };

    const removeRow = row => {
        gsap.to(row, {
            opacity: 0,
            x: 20,
            duration: 0.3,
            onComplete: () => {
                row.remove();
                updateSelectedProducts();
                triggerChange();
            }
        });
    };

    const getRows = () => {
        const container = getContainer();
        if (!container) {
            return [];
        }
        return Array.from(container.querySelectorAll('.product-row'));
    };

    const triggerChange = () => {
        const subtotal = getRows().reduce((sum, row) => sum + calculateRowTotal(row), 0);
        renderSubtotal(subtotal);
        if (typeof state.onChange === 'function') {
            state.onChange();
        }
    };

    const renderSubtotal = amount => {
        state.subtotalSelectors.forEach(selector => {
            const el = document.querySelector(selector);
            if (el) {
                el.textContent = utils.formatCurrency(amount);
            }
        });
    };

    const getProducts = () => {
        return getRows().map(row => {
            const { select, quantity, extrasList, start, end } = getRowElements(row);
            const qty = Math.max(1, Number(quantity?.value) || 1);
            const rowStart = start?.value || rental.getPeriod().start;
            const rowEnd = end?.value || rental.getPeriod().end;
            const extrasIds = Array.from(extrasList?.querySelectorAll('.extra-checkbox:checked') || [])
                .map(input => input.dataset?.id)
                .filter(Boolean);
            const days = calculateRowDays(row);

            return {
                product_id: select.value,
                quantity: qty,
                extras: extrasIds,
                start_date: rowStart,
                expected_return_date: rowEnd,
                days
            };
        }).filter(item => item.product_id);
    };

    const loadExtras = row => {
        const { select, extrasList, extrasContainer, extrasNote, extrasPreview } = getRowElements(row);
        const productId = select.value;

        if (!productId || !extrasList) {
            if (extrasNote) {
                extrasNote.textContent = 'Select a product to load extras.';
            }
            if (extrasList) {
                extrasList.innerHTML = '';
            }
            if (extrasPreview) {
                extrasPreview.textContent = 'Extras data will appear here.';
            }
            return;
        }

        const activeOption = select.selectedOptions[0];
        const optionExtras = activeOption?.dataset?.extras;

        const updateExtrasPreviewText = extras => {
            if (!extrasPreview) {
                return;
            }
            if (!extras.length) {
                extrasPreview.textContent = 'No extras available for this product yet.';
                return;
            }
            const parts = extras.map(extra => {
                const daily = extra.price_per_day ? `$${extra.price_per_day}/day` : '$0/day';
                const oneTime = extra.one_time_fee ? ` +$${Number(extra.one_time_fee).toFixed(2)} one-time` : '';
                return `${extra.name} (${daily}${oneTime})`;
            });
            extrasPreview.textContent = `Included extras: ${parts.join(', ')}`;
        };

        const renderExtras = extras => {
            if (!extrasList) {
                return;
            }
            if (extras.length) {
                extrasList.innerHTML = extras.map(extra => {
                    return `
                        <label class="inline-flex items-center gap-2 text-xs text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800/40 rounded-lg px-3 py-2 cursor-pointer border border-transparent transition-colors duration-150 hover:border-gray-300 dark:hover:border-gray-600">
                            <input type="checkbox" class="extra-checkbox" data-id="${extra.id}" data-price="${extra.price_per_day}" data-one-time="${extra.one_time_fee || 0}" checked>
                            <span>
                                ${extra.name}
                                <span class="block text-[0.65rem] text-gray-500 dark:text-gray-400">
                                    ${formatExtrasOption(extra)}
                                </span>
                            </span>
                        </label>`;
                }).join('');
                if (extrasNote) {
                    extrasNote.textContent = 'Extras loaded. Toggle the checkbox to include them.';
                }
                updateExtrasPreviewText(extras);
            } else {
                extrasList.innerHTML = '';
                if (extrasNote) {
                    extrasNote.textContent = 'No extras available for this product yet.';
                }
                updateExtrasPreviewText([]);
            }
            extrasList.querySelectorAll('.extra-checkbox').forEach(input => {
                input.addEventListener('change', triggerChange);
            });
            triggerChange();
        };

        if (optionExtras) {
            try {
                const parsed = JSON.parse(optionExtras);
                renderExtras(parsed);
                return;
            } catch (err) {
                console.warn('Could not parse option extras', err);
            }
        }

        fetch(`/orders/api/get-product-extras/?product_id=${productId}`)
            .then(response => response.json())
            .then(data => {
                if (!data.extras) {
                    renderExtras([]);
                    return;
                }
                renderExtras(data.extras);
            })
            .catch(err => {
                console.error('Failed to load extras', err);
            });
    };

    const checkStock = row => {
        const { select, quantity, stockStatus } = getRowElements(row);
        const qty = Number(quantity?.value) || 0;
        if (!select?.value || qty <= 0) {
            stockStatus.textContent = '';
            return;
        }
        const availableMatch = select.selectedOptions[0]?.text.match(/\((\d+) avail\)/);
        if (!availableMatch) {
            return;
        }
        const available = Number(availableMatch[1]) || 0;
        if (qty > available) {
            stockStatus.innerHTML = `<span class="text-red-600">⚠️ Short by ${qty - available} units</span>`;
            gsap.to(stockStatus, { scale: 1.1, duration: 0.15, yoyo: true, repeat: 1 });
        } else {
            stockStatus.innerHTML = `<span class="text-green-600">✓ Available</span>`;
        }
    };

    const applyGlobalDates = () => {
        const container = getContainer();
        if (!container) {
            return;
        }
        getRows().forEach(row => {
            if (row.dataset.syncGlobal === 'false') {
                return;
            }
            const { start, end } = getRowElements(row);
            if (start) start.value = rental.getPeriod().start;
            if (end) end.value = rental.getPeriod().end;
            updateRowDuration(row);
        });
        triggerChange();
    };

    const reset = () => {
        const container = getContainer();
        if (!container) {
            return;
        }
        container.innerHTML = '';
        addRow();
        triggerChange();
    };

    const init = options => {
        state.containerId = options?.containerId || 'productsContainer';
        state.container = document.getElementById(state.containerId);
        const addBtn = document.getElementById(state.addButtonId);
        state.onChange = options?.onChange;

        if (addBtn) {
            addBtn.addEventListener('click', () => addRow());
        }

        addRow();
    };

    const isReady = () => Boolean(getContainer());

    global.OrderProductsSection = {
        init,
        getItems: getProducts,
        applyGlobalDates,
        reset,
        triggerChange,
        isReady: () => Boolean(getContainer())
    };
})(window, window.OrderUtils || (window.OrderUtils = {}), window.OrderRentalPeriod || (window.OrderRentalPeriod = {}));
