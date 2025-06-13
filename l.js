document.addEventListener('DOMContentLoaded', function() {
    // ฟังก์ชันสร้างกราฟเส้น
    function createLineChart(canvasId, labels, datasets) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '฿' + value.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    }

    // ฟังก์ชันสร้างกราฟแท่ง
    function createBarChart(canvasId, labels, datasets) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '฿' + value.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    }

    // ฟังก์ชันอัพเดตตัวเลขสถิติ
    function updateMetric(elementId, value, trend) {
        const element = document.getElementById(elementId);
        if (element) {
            const valueElement = element.querySelector('.metric-value');
            const trendElement = element.querySelector('.metric-trend');
            
            if (valueElement) {
                valueElement.textContent = new Intl.NumberFormat('th-TH', {
                    style: 'currency',
                    currency: 'THB'
                }).format(value);
            }
            
            if (trendElement) {
                const trendValue = (trend * 100).toFixed(1);
                const trendClass = trend >= 0 ? 'positive' : 'negative';
                const trendIcon = trend >= 0 ? '↑' : '↓';
                trendElement.textContent = `${trendIcon} ${Math.abs(trendValue)}%`;
                trendElement.className = `metric-trend ${trendClass}`;
            }
        }
    }

    // ฟังก์ชันดึงข้อมูลจาก API
    async function fetchData() {
        try {
            const errorElement = document.getElementById('error-message');
            if (errorElement) {
                errorElement.textContent = '';
            }

            // ดึงข้อมูลตัวเลขสถิติ
            const [totalRevenue, netProfit, newCustomers, cashFlow] = await Promise.all([
                fetch('http://127.0.0.1:5000/api/total-revenue').then(r => r.json()),
                fetch('http://127.0.0.1:5000/api/net-profit').then(r => r.json()),
                fetch('http://127.0.0.1:5000/api/new-customers').then(r => r.json()),
                fetch('http://127.0.0.1:5000/api/cash-flow').then(r => r.json())
            ]);

            // อัพเดตตัวเลขสถิติ
            updateMetric('total-revenue', totalRevenue.value, totalRevenue.trend);
            updateMetric('net-profit', netProfit.value, netProfit.trend);
            updateMetric('new-customers', newCustomers.value, newCustomers.trend);
            updateMetric('cash-flow', cashFlow.value, cashFlow.trend);

            // ดึงและสร้างกราฟ Revenue
            const revenueData = await fetch('http://127.0.0.1:5000/api/revenue-data').then(r => r.json());
            createLineChart('revenue-chart', revenueData.labels, [{
                label: 'Revenue',
                data: revenueData.values,
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            }]);

            // ดึงและสร้างกราฟ Expenses
            const expensesData = await fetch('http://127.0.0.1:5000/api/expenses-data').then(r => r.json());
            createBarChart('expenses-chart', expensesData.labels, [{
                label: 'Expenses',
                data: expensesData.values,
                backgroundColor: 'rgb(255, 99, 132)'
            }]);

            // ดึงและสร้างกราฟ Revenue vs Target
            const targetData = await fetch('http://127.0.0.1:5000/api/revenue-target-data').then(r => r.json());
            createLineChart('revenue-target-chart', targetData.labels, [
                {
                    label: 'Actual Revenue',
                    data: targetData.actual,
                    borderColor: 'rgb(75, 192, 192)',
                    fill: false
                },
                {
                    label: 'Target Revenue',
                    data: targetData.target,
                    borderColor: 'rgb(255, 99, 132)',
                    borderDash: [5, 5],
                    fill: false
                }
            ]);

        } catch (error) {
            console.error('Error fetching data:', error);
            const errorElement = document.getElementById('error-message');
            if (errorElement) {
                errorElement.textContent = `Error loading dashboard data: ${error.message}`;
            }
        }
    }

    // เรียกใช้ฟังก์ชันดึงข้อมูล
    fetchData();

    // รีเฟรชข้อมูลทุก 5 นาที
    setInterval(fetchData, 5 * 60 * 1000);
});