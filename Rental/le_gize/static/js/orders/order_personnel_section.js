(function(global) {
    const state = {
        container: null,
        containerId: 'personnelContainer',
        templateId: 'personnelRowTemplate',
        addButtonId: 'addPersonnelBtn',
        totalDisplaySelector: '#personnelPercentageTotal',
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

    const getRowElements = row => ({
        select: row.querySelector('.personnel-select'),
        percentage: row.querySelector('.personnel-percentage')
    });

    const getAllRows = () => {
        const container = getContainer();
        if (!container) {
            return [];
        }
        return Array.from(container.querySelectorAll('.personnel-row'));
    };

    const getLeaderPercentage = () => {
        const rows = getAllRows();
        if (!rows.length) {
            return 0;
        }
        const leaderInput = rows[0].querySelector('.personnel-percentage');
        return Number(leaderInput?.value) || 0;
    };

    const updateTeamPercentages = () => {
        const rows = getAllRows();
        if (!rows.length) {
            return;
        }
        const leaderValue = getLeaderPercentage();
        const share = rows.length > 1 ? leaderValue / rows.length : leaderValue;
        rows.forEach((row, index) => {
            const { percentage } = getRowElements(row);
            if (index === 0) {
                percentage.disabled = false;
                percentage.value = leaderValue.toFixed(2);
                return;
            }
            percentage.value = share.toFixed(2);
            percentage.disabled = true;
        });
    };

    const updatePersonnelOptions = () => {
        const container = getContainer();
        if (!container) {
            return;
        }
        const selectedIds = Array.from(container.querySelectorAll('.personnel-select'))
            .map(select => select.value)
            .filter(Boolean);

        container.querySelectorAll('.personnel-select').forEach(select => {
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

    const triggerChange = () => {
        renderTotalAllocation();
        if (typeof state.onChange === 'function') {
            state.onChange();
        }
    };

    const renderTotalAllocation = () => {
        const totalEl = document.querySelector(state.totalDisplaySelector);
        if (!totalEl) {
            return;
        }
        const total = getTotalWeight();
        totalEl.textContent = `${total.toFixed(2)}%`;
        const container = getContainer();
        if (container && total !== 100 && container.querySelectorAll('.personnel-row').length > 0) {
            totalEl.classList.add('text-red-600');
        } else {
            totalEl.classList.remove('text-red-600');
        }
    };

    const addRow = () => {
        const container = getContainer();
        if (!container) {
            return;
        }
        const template = document.getElementById(state.templateId);
        if (!template) {
            return;
        }
        const clone = template.content.cloneNode(true);
        container.appendChild(clone);
        const row = container.querySelector('.personnel-row:last-child');
        const { select, percentage } = getRowElements(row);
        const existingRows = getAllRows();
        if (existingRows.length > 1) {
            const leadPercentage = Number(existingRows[0].querySelector('.personnel-percentage')?.value) || 0;
            if (leadPercentage > 0 && Number(percentage.value) === 0) {
                percentage.value = leadPercentage.toFixed(2);
            }
        }

        const handleSelectChange = () => {
            const selected = select.selectedOptions[0];
            const commission = Number(selected?.dataset?.commission) || 0;
            if (commission > 0 && Number(percentage.value) === 0) {
                percentage.value = commission.toFixed(2);
            }
            updateTeamPercentages();
            triggerChange();
            updatePersonnelOptions();
        };

        select?.addEventListener('change', () => {
            handleSelectChange();
            updateTeamPercentages();
        });
        percentage?.addEventListener('input', () => {
            updateTeamPercentages();
            triggerChange();
        });
        row.querySelector('.remove-personnel')?.addEventListener('click', () => {
            gsap.to(row, {
                opacity: 0,
                x: 20,
                duration: 0.25,
                onComplete: () => {
                    row.remove();
                    updatePersonnelOptions();
                    updateTeamPercentages();
                    triggerChange();
                }
            });
        });

        gsap.from(row, {
            opacity: 0,
            x: -20,
            duration: 0.3,
            ease: 'power2.out'
        });

        updatePersonnelOptions();
        updateTeamPercentages();
        triggerChange();
    };

    const getTotalWeight = () => getLeaderPercentage();

    const getAllocations = () => {
        const rows = getAllRows();
        if (!rows.length) {
            return [];
        }
        const basePercentage = Number(rows[0].querySelector('.personnel-percentage')?.value) || 0;
        const perPerson = rows.length > 1 ? basePercentage / rows.length : basePercentage;
        return rows.map(row => {
            const { select } = getRowElements(row);
            const name = select.selectedOptions[0]?.dataset?.name || '';
            return {
                personnel_id: select.value,
                percentage: perPerson,
                name
            };
        }).filter(entry => entry.personnel_id);
    };

    const reset = () => {
        const container = getContainer();
        if (!container) {
            return;
        }
        container.innerHTML = '';
        addRow();
    };

    const init = options => {
        state.containerId = options?.containerId || 'personnelContainer';
        state.container = document.getElementById(state.containerId);
        const addBtn = document.getElementById(state.addButtonId);
        state.onChange = options?.onChange;

        if (addBtn) {
            addBtn.addEventListener('click', () => addRow());
        }

        addRow();
    };

    global.OrderPersonnelSection = {
        init,
        getAllocations,
        getTotalWeight,
        reset,
        subscribe: callback => {
            state.onChange = callback;
        }
    };
})(window);
