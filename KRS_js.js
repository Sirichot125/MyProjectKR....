// script.js
document.addEventListener('DOMContentLoaded', function () {
    const API_BASE_URL = 'http://127.0.0.1:5000/api'; // URL ของ Flask API ของคุณ

    // Helper function to format numbers (e.g., for currency)
    function formatNumber(num) {
        if (typeof num !== 'number') return '-';
        return num.toLocaleString('th-TH', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    function formatInteger(num) {
        if (typeof num !== 'number') return '-';
        return num.toLocaleString('th-TH');
    }

    // Helper function to format trend percentage
    function formatTrend(trend) {
        if (typeof trend !== 'number') return '-';
        const trendPercent = (trend * 100).toFixed(2);
        let trendClass = 'text-gray-600';
        let trendIcon = '';
        if (trend > 0) {
            trendClass = 'text-green-500';
            trendIcon = '▲ ';
        } else if (trend < 0) {
            trendClass = 'text-red-500';
            trendIcon = '▼ ';
        }
        return `<span class="${trendClass}">${trendIcon}${Math.abs(trendPercent)}</span>`;
    }
    
    // Function to update a KPI card
    function updateKPI(elementId, value, formatter = formatNumber) {
        const el = document.getElementById(elementId);
        if (el) {
            el.textContent = formatter(value);
        } else {
            console.warn(`Element with ID ${elementId} not found.`);
        }
    }

    function updateKPITrend(elementId, trendValue) {
         const el = document.getElementById(elementId);
        if (el) {
            el.innerHTML = formatTrend(trendValue);
        } else {
            console.warn(`Element with ID ${elementId} not found.`);
        }
    }


    // Fetch and display Total Revenue
    fetch(`${API_BASE_URL}/total-revenue`)
        .then(response => response.json())
        .then(data => {
            updateKPI('total-revenue-value', data.value);
            updateKPITrend('total-revenue-trend', data.trend);
        })
        .catch(error => console.error('Error fetching Total Revenue:', error));

    // Fetch and display Net Profit
    fetch(`${API_BASE_URL}/net-profit`)
        .then(response => response.json())
        .then(data => {
            updateKPI('net-profit-value', data.value);
            updateKPITrend('net-profit-trend', data.trend);
        })
        .catch(error => console.error('Error fetching Net Profit:', error));

    // Fetch and display New Customers
    fetch(`${API_BASE_URL}/new-customers`)
        .then(response => response.json())
        .then(data => {
            updateKPI('new-customers-value', data.value, formatInteger);
            updateKPITrend('new-customers-trend', data.trend);
        })
        .catch(error => console.error('Error fetching New Customers:', error));

    // Fetch and display Net Profit Margin
    fetch(`${API_BASE_URL}/net-profit-margin`)
        .then(response => response.json())
        .then(data => {
            updateKPI('net-profit-margin-value', (data.value * 100), (val) => `${formatNumber(val)}%`);
        })
        .catch(error => console.error('Error fetching Net Profit Margin:', error));

    // Chart configurations
    const defaultChartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: {
                beginAtZero: true,
                ticks: {
                    callback: function(value) {
                        return value.toLocaleString('th-TH');
                    }
                }
            }
        },
        plugins: {
            legend: {
                position: 'top',
            },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        let label = context.dataset.label || '';
                        if (label) {
                            label += ': ';
                        }
                        if (context.parsed.y !== null) {
                            label += formatNumber(context.parsed.y);
                        }
                        return label;
                    }
                }
            }
        }
    };

    // Fetch and display Revenue and Net Profit Chart
    fetch(`${API_BASE_URL}/revenue-data`)
        .then(response => response.json())
        .then(data => {
            const ctx = document.getElementById('revenue-profit-chart')?.getContext('2d');
            if (ctx) {
                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: data.labels, // ['Jan', 'Feb', ...]
                        datasets: [
                            {
                                label: 'ยอดขาย (Revenue)',
                                data: data.values,
                                borderColor: 'rgb(75, 192, 192)',
                                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                                tension: 0.1,
                                fill: true,
                            },
                            {
                                label: 'กำไรสุทธิ (Net Profit)',
                                data: data.netProfitValues,
                                borderColor: 'rgb(255, 99, 132)',
                                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                                tension: 0.1,
                                fill: true,
                            }
                        ]
                    },
                    options: defaultChartOptions
                });
            }
        })
        .catch(error => console.error('Error fetching Revenue Data:', error));

    // Fetch and display Expenses Chart
    fetch(`${API_BASE_URL}/expenses-data`)
        .then(response => response.json())
        .then(data => {
            const ctx = document.getElementById('expenses-chart')?.getContext('2d');
            if (ctx) {
                new Chart(ctx, {
                    type: 'bar', // Changed to bar for variety
                    data: {
                        labels: data.labels,
                        datasets: [{
                            label: 'ค่าใช้จ่าย (Expenses)',
                            data: data.values,
                            backgroundColor: 'rgba(255, 159, 64, 0.5)',
                            borderColor: 'rgb(255, 159, 64)',
                            borderWidth: 1
                        }]
                    },
                    options: defaultChartOptions
                });
            }
        })
        .catch(error => console.error('Error fetching Expenses Data:', error));

    // Fetch and display Revenue Target Chart
    fetch(`${API_BASE_URL}/revenue-target-data`)
        .then(response => response.json())
        .then(data => {
            const ctx = document.getElementById('revenue-target-chart')?.getContext('2d');
            if(ctx) {
                new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: data.labels,
                        datasets: [
                            {
                                label: 'ยอดขายจริง (Actual)',
                                data: data.actual,
                                backgroundColor: 'rgba(54, 162, 235, 0.6)',
                                borderColor: 'rgb(54, 162, 235)',
                                borderWidth: 1
                            },
                            {
                                label: 'เป้าหมาย (Target)',
                                data: data.target,
                                backgroundColor: 'rgba(201, 203, 207, 0.6)',
                                borderColor: 'rgb(201, 203, 207)',
                                borderWidth: 1
                            }
                        ]
                    },
                    options: defaultChartOptions
                });
            }
        })
        .catch(error => console.error('Error fetching Revenue Target Data:', error));

    // --- Operational KPIs and Charts ---
    // Uptime
    fetch(`${API_BASE_URL}/uptime`)
        .then(response => response.json())
        .then(data => {
            updateKPI('uptime-value', data.value, (val) => `${formatNumber(val)}%`); // Assuming Uptime is a percentage
            updateKPITrend('uptime-trend', data.trend);
        })
        .catch(error => console.error('Error fetching Uptime:', error));
    
    fetch(`${API_BASE_URL}/uptime-data`)
        .then(response => response.json())
        .then(data => {
            const ctx = document.getElementById('uptime-chart')?.getContext('2d');
            if(ctx) {
                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: data.labels,
                        datasets: [{
                            label: 'Uptime (%)',
                            data: data.values,
                            borderColor: 'rgb(60, 179, 113)',
                            backgroundColor: 'rgba(60, 179, 113, 0.2)',
                            fill: true,
                            tension: 0.1
                        }]
                    },
                    options: defaultChartOptions
                });
            }
        })
        .catch(error => console.error('Error fetching Uptime Data:', error));


    // Response Time
    fetch(`${API_BASE_URL}/response-time`)
        .then(response => response.json())
        .then(data => {
            updateKPI('response-time-value', data.value, formatInteger); // Assuming ms
            updateKPITrend('response-time-trend', data.trend);
        })
        .catch(error => console.error('Error fetching Response Time:', error));
    
    // Bugs
     fetch(`${API_BASE_URL}/bugs`)
        .then(response => response.json())
        .then(data => {
            updateKPI('bugs-value', data.value, formatInteger);
            updateKPITrend('bugs-trend', data.trend);
        })
        .catch(error => console.error('Error fetching Bugs:', error));

    fetch(`${API_BASE_URL}/bug-count-data`) // Endpoint from Python is bugsData
        .then(response => response.json())
        .then(data => {
            const ctx = document.getElementById('bugs-chart')?.getContext('2d');
            if(ctx) {
                new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: data.labels,
                        datasets: [{
                            label: 'จำนวน Bugs',
                            data: data.values,
                            backgroundColor: 'rgba(255, 99, 71, 0.6)',
                            borderColor: 'rgb(255, 99, 71)',
                            borderWidth: 1
                        }]
                    },
                    options: defaultChartOptions
                });
            }
        })
        .catch(error => console.error('Error fetching Bug Count Data:', error));
        
    // Deployments
    fetch(`${API_BASE_URL}/deployments`)
        .then(response => response.json())
        .then(data => {
            updateKPI('deployments-value', data.value, formatInteger);
            updateKPITrend('deployments-trend', data.trend);
        })
        .catch(error => console.error('Error fetching Deployments:', error));

    fetch(`${API_BASE_URL}/deployment-frequency-data`) // Endpoint from Python is deploymentsData
        .then(response => response.json())
        .then(data => {
            const ctx = document.getElementById('deployments-chart')?.getContext('2d');
            if(ctx) {
                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: data.labels,
                        datasets: [{
                            label: 'จำนวน Deployments',
                            data: data.values,
                            borderColor: 'rgb(123, 104, 238)',
                            backgroundColor: 'rgba(123, 104, 238, 0.2)',
                            fill: true,
                            tension: 0.1
                        }]
                    },
                    options: defaultChartOptions
                });
            }
        })
        .catch(error => console.error('Error fetching Deployment Frequency Data:', error));

});