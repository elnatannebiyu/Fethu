(function(global) {
    const formatCurrency = value => {
        const amount = Number(value);
        if (Number.isNaN(amount)) {
            return '$0.00';
        }
        return `$${amount.toFixed(2)}`;
    };

    const clamp = (value, min, max) => Math.min(Math.max(value, min), max);

    const getCookie = name => {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === `${name}=`) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    };

    const calculateDays = (start, end) => {
        if (!start || !end) {
            return 1;
        }
        const startDate = new Date(start);
        const endDate = new Date(end);
        if (Number.isNaN(startDate.getTime()) || Number.isNaN(endDate.getTime())) {
            return 1;
        }
        const diff = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24));
        return diff > 0 ? diff : 1;
    };

    global.OrderUtils = global.OrderUtils || {};
    global.OrderUtils.formatCurrency = formatCurrency;
    global.OrderUtils.clamp = clamp;
    global.OrderUtils.getCookie = getCookie;
    global.OrderUtils.calculateDays = calculateDays;
})(window);
