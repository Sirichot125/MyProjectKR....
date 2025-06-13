// sc.js - Dashboard Script

const API_BASE_URL = 'http://127.0.0.1:5000/api'; // URL หลักของ Flask API

// --- ฟังก์ชัน Utility ---
function updateLastUpdated() {
    const lastUpdatedElement = document.getElementById('last-updated');
    if (lastUpdatedElement) {
        lastUpdatedElement.textContent = new Date().toLocaleString('th-TH', {
            dateStyle: 'medium', timeStyle: 'short'
        });
    }
}

function showToast(message, type = 'success') {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        console.warn('Toast container not found. Please ensure <div id="toast-container" class="fixed top-5 right-5 z-[100] space-y-2"></div> exists in your HTML.');
        alert(message); // Fallback
        return;
    }
    const toastId = 'toast-' + Date.now();
    const toast = document.createElement('div');
    toast.id = toastId;

    let bgColor = 'bg-blue-500 dark:bg-blue-600'; // Default to info
    if (type === 'success') bgColor = 'bg-green-500 dark:bg-green-600';
    else if (type === 'error') bgColor = 'bg-red-500 dark:bg-red-600';
    else if (type === 'warning') bgColor = 'bg-yellow-500 dark:bg-yellow-600';

    toast.className = `p-4 rounded-md shadow-lg text-sm font-medium text-white transition-all duration-300 ease-in-out transform translate-x-full ${bgColor}`;
    toast.textContent = message;
    toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.classList.remove('translate-x-full');
        toast.classList.add('translate-x-0');
    }, 100);

    setTimeout(() => {
        toast.classList.add('opacity-0');
        toast.addEventListener('transitionend', () => toast.remove());
    }, 3500);
}

async function fetchData(endpoint, method = 'GET', body = null) {
    const options = {
        method: method.toUpperCase(),
        headers: {}
    };

    if (body) {
        options.headers['Content-Type'] = 'application/json';
        options.body = JSON.stringify(body);
    }

    console.log(`Fetching: ${API_BASE_URL}${endpoint} (${options.method})`);
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);

        if (!response.ok) {
            let errorData = { message: `Server error: ${response.status} ${response.statusText}`, status: response.status };
            try {
                const errorJson = await response.json();
                errorData = { ...errorData, ...errorJson };
            } catch (e) {
                const errorText = await response.text();
                errorData.message = errorText || errorData.message;
            }
            console.error(`API Error ${endpoint}:`, errorData);
            return { success: false, error: errorData.message || 'Unknown server error', status: response.status, data: errorData };
        }

        if (response.status === 204) {
            return { success: true, status: response.status, data: null };
        }

        const data = await response.json();
        return { success: true, status: response.status, data: data };

    } catch (error) {
        console.error(`Network Error ${endpoint}:`, error);
        if (endpoint.includes('via.placeholder.com') && error.message.includes('Failed to fetch')) {
            console.warn(`Placeholder image could not be loaded from ${endpoint}.`);
            return { success: false, error: 'Placeholder image load failed', status: 'NETWORK_ERROR', data: null };
        }
        return { success: false, error: error.message || 'Network error', status: 'NETWORK_ERROR', data: null };
    }
}

function updateKpiTrend(trendElementId, trendValue) {
    const trendElement = document.getElementById(trendElementId);
    if (trendElement) {
        if (trendValue === undefined || trendValue === null || isNaN(parseFloat(trendValue))) {
            trendElement.textContent = '-';
            trendElement.className = 'text-sm font-medium text-slate-500 dark:text-slate-400';
            return;
        }
        const value = parseFloat(trendValue);
        const percentageValue = value * 100;

        trendElement.textContent = `${percentageValue >= 0 ? '+' : ''}${percentageValue.toFixed(1)}%`;
        trendElement.className = 'text-sm font-medium ';
        if (percentageValue > 0) {
            trendElement.classList.add('trend-up');
        } else if (percentageValue < 0) {
            trendElement.classList.add('trend-down');
        } else {
            trendElement.classList.add('text-slate-500', 'dark:text-slate-400');
        }
    }
}

async function updateKpiData() {
    let response;
    response = await fetchData('/total-revenue');
    const totalRevenueValueEl = document.getElementById('total-revenue-value');
    if (response.success && response.data && response.data.value !== undefined && totalRevenueValueEl) {
        totalRevenueValueEl.textContent = `฿${parseFloat(response.data.value).toLocaleString('th-TH', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        updateKpiTrend('total-revenue-trend', response.data.trend);
    } else if (totalRevenueValueEl) {
        totalRevenueValueEl.textContent = 'Error';
        updateKpiTrend('total-revenue-trend', null);
        if (response.error) console.error("Error fetching total revenue:", response.error);
    }

    response = await fetchData('/net-profit');
    const netProfitValueEl = document.getElementById('net-profit-value');
    if (response.success && response.data && response.data.value !== undefined && netProfitValueEl) {
        netProfitValueEl.textContent = `฿${parseFloat(response.data.value).toLocaleString('th-TH', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        updateKpiTrend('net-profit-trend', response.data.trend);
    } else if (netProfitValueEl) {
        netProfitValueEl.textContent = 'Error';
        updateKpiTrend('net-profit-trend', null);
        if (response.error) console.error("Error fetching net profit:", response.error);
    }

    response = await fetchData('/total-quantity-ordered');
    const tqoValueEl = document.getElementById('total-quantity-ordered-value');
    if (response.success && response.data && response.data.value !== undefined && tqoValueEl) {
        tqoValueEl.textContent = `${parseFloat(response.data.value).toLocaleString('th-TH', { maximumFractionDigits: 0 })} หน่วย`;
        updateKpiTrend('total-quantity-ordered-trend', response.data.trend);
    } else if (tqoValueEl) {
        tqoValueEl.textContent = 'Error';
        updateKpiTrend('total-quantity-ordered-trend', null);
        if (response.error) console.error("Error fetching total quantity ordered:", response.error);
    }

    response = await fetchData('/new-customers');
    const newCustomersValueEl = document.getElementById('new-customers-value');
    if (response.success && response.data && response.data.value !== undefined && newCustomersValueEl) {
        newCustomersValueEl.textContent = `${parseInt(response.data.value).toLocaleString('th-TH')} คน/รายการ`;
        updateKpiTrend('new-customers-trend', response.data.trend);
    } else if (newCustomersValueEl) {
        newCustomersValueEl.textContent = 'Error';
        updateKpiTrend('new-customers-trend', null);
        if (response.error) console.error("Error fetching new customers:", response.error);
    }
    updateLastUpdated();
}

async function renderCharts() {
    console.log("renderCharts called");
    let response;

    function displayChartError(canvasId, message = 'ไม่สามารถโหลดข้อมูลกราฟได้') {
        const canvas = document.getElementById(canvasId);
        if (canvas && canvas.getContext) {
            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.save();
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.font = '14px "Helvetica Neue", Helvetica, Arial, sans-serif'; // Example font
            ctx.fillStyle = document.documentElement.classList.contains('dark') ? '#94a3b8' : '#64748b';
            ctx.fillText(message, canvas.width / 2, canvas.height / 2);
            ctx.restore();
        }
    }

    // --- 1. กราฟยอดขายและกำไร ---
    response = await fetchData('/revenue-data');
    const revenueProfitCtx = document.getElementById('revenue-profit-chart');
    if (revenueProfitCtx) {
        if (window.revenueProfitChart instanceof Chart) { window.revenueProfitChart.destroy(); }
        if (response.success && response.data && response.data.labels && response.data.values && response.data.netProfitValues) {
            const chartData = response.data;
            window.revenueProfitChart = new Chart(revenueProfitCtx, {
                type: 'line', data: {
                    labels: chartData.labels, datasets: [
                        { label: 'ยอดขาย (บาท)', data: chartData.values, borderColor: 'rgb(79, 70, 229)', backgroundColor: 'rgba(79, 70, 229, 0.1)', tension: 0.1, fill: true },
                        { label: 'กำไรสุทธิ (บาท)', data: chartData.netProfitValues, borderColor: 'rgb(22, 163, 74)', backgroundColor: 'rgba(22, 163, 74, 0.1)', tension: 0.1, fill: true }
                    ]
                }, options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true, ticks: { callback: value => `฿${parseFloat(value).toLocaleString('th-TH')}` } } } }
            });
        } else {
            displayChartError('revenue-profit-chart');
            if (!response.success) console.warn("Error fetching revenue-profit-chart:", response.error);
            else console.warn("Data for revenue-profit-chart missing properties. Received:", response.data);
        }
    }

    // --- 2. กราฟค่าใช้จ่าย ---
    response = await fetchData('/expenses-data');
    const expensesCtx = document.getElementById('expenses-chart');
    if (expensesCtx) {
        if (window.expensesChart instanceof Chart) { window.expensesChart.destroy(); }
        if (response.success && response.data && response.data.labels && response.data.values) {
            const chartData = response.data;
            window.expensesChart = new Chart(expensesCtx, {
                type: 'bar', data: { labels: chartData.labels, datasets: [{ label: 'ค่าใช้จ่าย (บาท)', data: chartData.values, backgroundColor: 'rgba(220, 38, 38, 0.6)', borderColor: 'rgb(220, 38, 38)', borderWidth: 1 }] },
                options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true, ticks: { callback: value => `฿${parseFloat(value).toLocaleString('th-TH')}` } } } }
            });
        } else {
            displayChartError('expenses-chart');
            if (!response.success) console.warn("Error fetching expenses-chart:", response.error);
            else console.warn("Data for expenses-chart missing properties. Received:", response.data);
        }
    }

    // --- 3. กราฟยอดขายเทียบกับเป้าหมาย ---
    response = await fetchData('/revenue-target-data');
    const revenueTargetCtx = document.getElementById('revenue-target-chart');
    if (revenueTargetCtx) {
        if (window.revenueTargetChart instanceof Chart) { window.revenueTargetChart.destroy(); }
        if (response.success && response.data && response.data.labels && response.data.actual && response.data.target) {
            const chartData = response.data;
            window.revenueTargetChart = new Chart(revenueTargetCtx, {
                type: 'bar', data: {
                    labels: chartData.labels, datasets: [
                        { label: 'ยอดขายจริง (บาท)', data: chartData.actual, backgroundColor: 'rgba(75, 192, 192, 0.6)', borderColor: 'rgb(75, 192, 192)', borderWidth: 1 },
                        { label: 'เป้าหมายยอดขาย (บาท)', data: chartData.target, backgroundColor: 'rgba(255, 159, 64, 0.6)', borderColor: 'rgb(255, 159, 64)', borderWidth: 1 }
                    ]
                }, options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true, ticks: { callback: value => `฿${parseFloat(value).toLocaleString('th-TH')}` } } } }
            });
        } else {
            displayChartError('revenue-target-chart');
            if (!response.success) console.warn("Error fetching revenue-target-chart:", response.error);
            else console.warn("Data for revenue-target-chart missing properties. Received:", response.data);
        }
    }

    // --- 4. กราฟอื่นๆ (วนลูป) ---
    const otherChartConfigs = {
        'quantity-ordered-chart': { endpoint: '/quantity-ordered-data', type: 'line', label: 'จำนวนสั่งซื้อ (หน่วย)', borderColor: 'rgb(153, 102, 255)', backgroundColor: 'rgba(153, 102, 255, 0.1)', unit: ' หน่วย', valueFormatting: value => parseFloat(value).toLocaleString('th-TH', {maximumFractionDigits: 0}) },
        'quantity-received-chart': { endpoint: '/quantity-received-data', type: 'line', label: 'จำนวนรับเข้า (หน่วย)', borderColor: 'rgb(255, 205, 86)', backgroundColor: 'rgba(255, 205, 86, 0.1)', unit: ' หน่วย', valueFormatting: value => parseFloat(value).toLocaleString('th-TH', {maximumFractionDigits: 0}) },
        'average-discount-chart': { endpoint: '/average-discount-data', type: 'bar', label: 'ส่วนลดเฉลี่ย (%)', borderColor: 'rgb(54, 162, 235)', backgroundColor: 'rgba(54, 162, 235, 0.1)', unit: '%', valueFormatting: value => (parseFloat(value) * 100).toFixed(1) }
    };

    for (const chartId in otherChartConfigs) {
        const config = otherChartConfigs[chartId];
        const chartCtx = document.getElementById(chartId);
        if (chartCtx) {
            response = await fetchData(config.endpoint);
            if (window[chartId] instanceof Chart) { window[chartId].destroy(); }
            if (response.success && response.data && response.data.labels && response.data.values) {
                const chartData = response.data;
                window[chartId] = new Chart(chartCtx, {
                    type: config.type, data: {
                        labels: chartData.labels, datasets: [{
                            label: config.label, data: chartData.values, borderColor: config.borderColor, backgroundColor: config.backgroundColor,
                            tension: (config.type === 'line' ? 0.1 : undefined), fill: (config.type === 'line' ? true : undefined), borderWidth: 1
                        }]
                    }, options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true, ticks: { callback: value => `${config.valueFormatting(value)}${config.unit || ''}` } } } }
                });
            } else {
                displayChartError(chartId);
                if (!response.success) console.warn(`Error fetching ${chartId}:`, response.error);
                else console.warn(`Data for ${chartId} missing properties. Received:`, response.data);
            }
        }
    }
}

// --- Product Modal Elements & Functions ---
const editProductModalEl = document.getElementById('editProductModal');
const editProductFormEl = document.getElementById('editProductForm');
const closeEditProductModalBtnEl = document.getElementById('closeEditProductModalBtn');
const cancelEditProductBtnEl = document.getElementById('cancelEditProductBtn');
const editProductOriginalItemCodeInputEl = document.getElementById('editProductOriginalItemCode');
const editItemCodeDisplayEl = document.getElementById('editItemCode');
const editProductNameInputEl = document.getElementById('editProductName');
const editCategoryInputEl = document.getElementById('editCategory');
const editPriceInputEl = document.getElementById('editPrice');
const editStockInputEl = document.getElementById('editStock');
const editStatusInputEl = document.getElementById('editStatus');


function initEditProductModal() {
    if (closeEditProductModalBtnEl) closeEditProductModalBtnEl.addEventListener('click', closeEditProductModal);
    if (cancelEditProductBtnEl) cancelEditProductBtnEl.addEventListener('click', closeEditProductModal);
    if (editProductFormEl) editProductFormEl.addEventListener('submit', handleEditProductFormSubmit);
    if (editProductModalEl) {
        editProductModalEl.addEventListener('click', (event) => {
            if (event.target === editProductModalEl) closeEditProductModal();
        });
    }
    const addNewProductBtn = document.getElementById('add-new-product-btn');
    if (addNewProductBtn) {
        addNewProductBtn.addEventListener('click', () => openEditProductModal(null));
    }
}

function openEditProductModal(product) { // product is null for "add new"
    if (!editProductModalEl) {
        console.error("editProductModalEl not found");
        return;
    }
    const modalTitle = editProductModalEl.querySelector('.text-2xl.font-bold'); // Selector from your HTML

    if (product) { // Editing
        if (modalTitle) modalTitle.textContent = 'แก้ไขข้อมูลสินค้า';
        // Use editProductOriginalItemCodeInputEl for the actual ItemCode to be used in API calls if it's different from display
        if (editProductOriginalItemCodeInputEl) editProductOriginalItemCodeInputEl.value = product.ItemCode;
        else if(editItemCodeDisplayEl) editItemCodeDisplayEl.value = product.ItemCode; // Fallback if hidden original not present

        if (editItemCodeDisplayEl) editItemCodeDisplayEl.value = product.ItemCode || '';
        if (editProductNameInputEl) editProductNameInputEl.value = product.ProductName || product.Description || ''; // Use ProductName from data
        if (editCategoryInputEl) editCategoryInputEl.value = product.Category || '';
        if (editPriceInputEl) editPriceInputEl.value = product.Price !== null ? parseFloat(product.Price) : ''; // Use Price from data
        if (editStockInputEl) editStockInputEl.value = product.Stock !== null ? parseInt(product.Stock) : '';
        if (editStatusInputEl) editStatusInputEl.value = product.Status || 'วางขาย';
    } else { // Adding
        if (modalTitle) modalTitle.textContent = 'เพิ่มสินค้าใหม่';
        if (editProductFormEl) editProductFormEl.reset();
        if (editProductOriginalItemCodeInputEl) editProductOriginalItemCodeInputEl.value = '';
        if (editItemCodeDisplayEl) editItemCodeDisplayEl.value = ''; // Clear or enable if new itemcode is user-defined
        // Consider if ItemCode is user-defined or server-generated for new products
    }

    editProductModalEl.style.display = 'flex';
    document.body.classList.add('modal-open');
    // Add opacity transition if you have corresponding CSS classes
    // editProductModalEl.classList.add('opacity-100');
}

function closeEditProductModal() {
    if (!editProductModalEl) return;
    // editProductModalEl.classList.remove('opacity-100'); // For opacity transition
    document.body.classList.remove('modal-open');
    // setTimeout(() => { // Use timeout if using opacity transition
        editProductModalEl.style.display = 'none';
        if (editProductFormEl) editProductFormEl.reset();
    // }, 300);
}

async function handleEditProductFormSubmit(event) {
    event.preventDefault();
    if (!editProductFormEl) return;

    // Prefer the hidden input for original item code if available, otherwise use the display one
    const originalItemCode = editProductOriginalItemCodeInputEl?.value || editItemCodeDisplayEl?.value;

    const productData = {
        // ItemCode should typically NOT be in the body for PUT if it's the identifier in URL
        // It MIGHT be in the body for POST if it's user-defined and not server-generated
        ProductName: editProductNameInputEl.value, // Ensure these IDs match your actual form
        Category: editCategoryInputEl.value,
        Price: parseFloat(editPriceInputEl.value),
        Stock: parseInt(editStockInputEl.value),
        Status: editStatusInputEl.value,
        Description: editProductNameInputEl.value // Assuming ProductName also serves as Description for simplicity
    };
     // If ItemCode is part of the form and should be sent (e.g. for POST and it's user-defined)
    if (!originalItemCode && editItemCodeDisplayEl && editItemCodeDisplayEl.value) {
         productData.ItemCode = editItemCodeDisplayEl.value;
    }


    const submitButton = editProductFormEl.querySelector('button[type="submit"]');
    const originalButtonText = submitButton.innerHTML;
    submitButton.disabled = true;
    submitButton.innerHTML = `กำลังบันทึก...`; // Add spinner icon here

    let response;
    let endpoint;
    let method;

    if (originalItemCode && originalItemCode !== "") { // Editing existing
        endpoint = `/products/${originalItemCode}`;
        method = 'PUT';
    } else { // Adding new
        endpoint = `/products`;
        method = 'POST';
    }

    response = await fetchData(endpoint, method, productData);
    submitButton.disabled = false;
    submitButton.innerHTML = originalButtonText;

    if (response.success) {
        const actionText = (originalItemCode && originalItemCode !== "") ? 'อัปเดตสินค้าสำเร็จ!' : 'เพิ่มสินค้าใหม่สำเร็จ!';
        showToast(actionText, 'success');
        closeEditProductModal();
        await loadProductData((originalItemCode && originalItemCode !== "") ? currentProductPage : 1, currentProductSearchTerm);
    } else {
        showToast(`เกิดข้อผิดพลาด: ${response.error || 'ไม่สามารถบันทึกสินค้าได้'}`, 'error');
    }
}

async function handleDeleteProduct(itemCode, productName) {
    if (!confirm(`คุณแน่ใจหรือไม่ว่าต้องการลบสินค้า "${productName}" (รหัส: ${itemCode})?\nการกระทำนี้ไม่สามารถย้อนกลับได้`)) {
        return;
    }
    const response = await fetchData(`/products/${itemCode}`, 'DELETE');
    if (response.success) {
        showToast(`สินค้า "${productName}" ถูกลบแล้ว`, 'success');
        const tableBody = document.getElementById('product-table-body');
        // Check if the deleted item was the last one on a page > 1
        if (tableBody && tableBody.rows.length === 0 && currentProductPage > 1) {
             await loadProductData(currentProductPage - 1, currentProductSearchTerm);
        } else {
             await loadProductData(currentProductPage, currentProductSearchTerm);
        }
    } else {
        showToast(`เกิดข้อผิดพลาดในการลบสินค้า: ${response.error || 'ไม่สามารถลบสินค้าได้'}`, 'error');
    }
}


let PRODUCT_ITEMS_PER_PAGE = parseInt(localStorage.getItem('product_items_per_page')) || 25; // Default from your HTML
let currentProductPage = 1;
let currentProductSearchTerm = '';

async function loadProductData(page = 1, searchTerm = '') {
    currentProductPage = page;
    currentProductSearchTerm = searchTerm;
    const endpoint = `/products?page=${page}&per_page=${PRODUCT_ITEMS_PER_PAGE}&search=${encodeURIComponent(searchTerm)}`;

    const tableBody = document.getElementById('product-table-body');
    const paginationInfo = document.getElementById('product-pagination-info');
    const paginationControls = document.getElementById('product-pagination-controls');

    if (!tableBody || !paginationInfo || !paginationControls) {
        console.error("Product table elements not found!");
        return;
    }
    tableBody.innerHTML = `<tr><td colspan="7" class="text-center py-10"><div class="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-500 border-r-transparent motion-reduce:animate-[spin_1.5s_linear_infinite]" role="status"><span class="!absolute !-m-px !h-px !w-px !overflow-hidden !whitespace-nowrap !border-0 !p-0 ![clip:rect(0,0,0,0)]">Loading...</span></div></td></tr>`;

    const response = await fetchData(endpoint);

    if (response.success && response.data && Array.isArray(response.data.data)) {
        const products = response.data.data;
        const totalItems = response.data.total;
        const currentPageFromApi = response.data.page;
        tableBody.innerHTML = '';

        if (products.length === 0) {
            const message = searchTerm ? 'ไม่พบข้อมูลสินค้าที่ตรงกับการค้นหา' : 'ไม่พบข้อมูลสินค้า';
            tableBody.innerHTML = `<tr><td colspan="7" class="text-center py-4">${message}</td></tr>`;
        } else {
            products.forEach(product => {
                const row = tableBody.insertRow();
                row.className = tableBody.rows.length % 2 === 0 ?
                    'bg-slate-50 dark:bg-slate-700 border-b dark:border-slate-600 hover:bg-slate-100 dark:hover:bg-slate-600' :
                    'bg-white dark:bg-slate-800 border-b dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-600';

                row.insertCell().textContent = product.ItemCode || '-';
                // Use ProductName from API for the name column
                row.insertCell().textContent = product.ProductName || product.Description || '-';
                row.insertCell().textContent = product.Category || '-';
                const priceCell = row.insertCell();
                priceCell.className = 'text-right';
                priceCell.textContent = product.Price !== null ? parseFloat(product.Price).toLocaleString('th-TH', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '-';
                const stockCell = row.insertCell();
                stockCell.className = 'text-right';
                stockCell.textContent = product.Stock !== null ? parseInt(product.Stock).toLocaleString('th-TH') : '-';

                const statusCell = row.insertCell();
                const statusSpan = document.createElement('span');
                statusSpan.textContent = product.Status || 'N/A';
                statusSpan.className = `px-2 py-1 text-xs font-medium rounded-full ${
                    product.Status === 'วางขาย' || product.Status === 'Active' ? 'text-green-700 bg-green-100 dark:text-green-100 dark:bg-green-700' :
                    product.Status === 'สินค้าหมด' ? 'text-yellow-700 bg-yellow-100 dark:text-yellow-100 dark:bg-yellow-600' :
                    'text-slate-700 bg-slate-100 dark:text-slate-200 dark:bg-slate-600'
                }`;
                statusCell.appendChild(statusSpan);

                const actionsCell = row.insertCell();
                actionsCell.className = 'px-4 sm:px-6 py-3 text-center space-x-2';

                const editButton = document.createElement('button');
                editButton.title = "แก้ไขสินค้า";
                editButton.className = "text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 focus:outline-none";
                editButton.innerHTML = `<svg class="w-5 h-5 inline-block" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"></path></svg>`;
                editButton.onclick = () => openEditProductModal(product);
                actionsCell.appendChild(editButton);

                const deleteButton = document.createElement('button');
                deleteButton.title = "ลบสินค้า";
                deleteButton.className = "text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300 focus:outline-none";
                deleteButton.innerHTML = `<svg class="w-5 h-5 inline-block" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>`;
                const productNameForDelete = product.ProductName || product.Description || 'สินค้านี้';
                deleteButton.onclick = () => handleDeleteProduct(product.ItemCode, productNameForDelete);
                actionsCell.appendChild(deleteButton);
            });
        }
        const startItem = totalItems > 0 ? (currentPageFromApi - 1) * PRODUCT_ITEMS_PER_PAGE + 1 : 0;
        const endItem = Math.min(startItem + PRODUCT_ITEMS_PER_PAGE - 1, totalItems);
        paginationInfo.innerHTML = `Showing <span class="font-semibold text-slate-900 dark:text-white">${startItem}-${endItem > totalItems ? totalItems : endItem}</span> of <span class="font-semibold text-slate-900 dark:text-white">${totalItems}</span>`;
        renderPaginationControls(paginationControls, currentPageFromApi, Math.ceil(totalItems / PRODUCT_ITEMS_PER_PAGE), loadProductData, currentProductSearchTerm);
    } else {
        tableBody.innerHTML = `<tr><td colspan="7" class="text-center py-4">ไม่สามารถโหลดข้อมูลสินค้าได้ (${response.error || 'ไม่ทราบสาเหตุ'})</td></tr>`;
        if (paginationInfo) paginationInfo.textContent = 'Showing 0-0 of 0';
        if (paginationControls) paginationControls.innerHTML = '';
        if (response.error) console.error("Error in loadProductData:", response.error);
    }
}

let HISTORY_ITEMS_PER_PAGE = parseInt(localStorage.getItem('history_items_per_page')) || 15;
let currentHistoryPage = 1;
let currentHistorySearchTerm = '';

async function loadStockHistoryData(page = 1, searchTerm = '') {
    currentHistoryPage = page;
    currentHistorySearchTerm = searchTerm;
    const endpoint = `/stock-history?page=${page}&per_page=${HISTORY_ITEMS_PER_PAGE}&search=${encodeURIComponent(searchTerm)}`;

    const tableBody = document.getElementById('stock-history-table-body');
    const paginationInfo = document.getElementById('stock-history-pagination-info');
    const paginationControls = document.getElementById('stock-history-pagination-controls');

    if (!tableBody || !paginationInfo || !paginationControls) {
        console.error("Stock history table elements not found!");
        return;
    }
    tableBody.innerHTML = `<tr><td colspan="6" class="text-center py-10"><div class="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-500 border-r-transparent motion-reduce:animate-[spin_1.5s_linear_infinite]" role="status"><span class="!absolute !-m-px !h-px !w-px !overflow-hidden !whitespace-nowrap !border-0 !p-0 ![clip:rect(0,0,0,0)]">Loading...</span></div></td></tr>`;

    const response = await fetchData(endpoint);

    if (response.success && response.data && Array.isArray(response.data.data)) {
        const historyEntries = response.data.data;
        const totalItems = response.data.total;
        const currentPageFromApi = response.data.page;
        tableBody.innerHTML = '';

        if (historyEntries.length === 0) {
            const message = searchTerm ? 'ไม่พบข้อมูลประวัติสต็อกที่ตรงกับการค้นหา' : 'ไม่พบข้อมูลประวัติสต็อก';
            tableBody.innerHTML = `<tr><td colspan="6" class="text-center py-4">${message}</td></tr>`;
        } else {
            historyEntries.forEach(entry => {
                const row = tableBody.insertRow();
                 row.className = tableBody.rows.length % 2 === 0 ?
                    'bg-slate-50 dark:bg-slate-700 border-b dark:border-slate-600 hover:bg-slate-100 dark:hover:bg-slate-600' :
                    'bg-white dark:bg-slate-800 border-b dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-600';

                row.insertCell().textContent = entry.Timestamp ? new Date(entry.Timestamp).toLocaleString('th-TH', { dateStyle: 'short', timeStyle: 'short'}) : '-';
                row.insertCell().textContent = `${entry.ProductIdentifier || ''} - ${entry.ProductName || ''}`.trim() || '-';
                const typeCell = row.insertCell();
                const typeSpan = document.createElement('span');
                typeSpan.textContent = entry.MovementType || 'N/A';
                let typeColorClass = 'text-slate-700 bg-slate-100 dark:text-slate-200 dark:bg-slate-600';
                const movementTypeLower = (entry.MovementType || '').toLowerCase();
                if (movementTypeLower.includes('รับเข้า') || movementTypeLower.includes('ordered') || movementTypeLower.includes('คืน')) {
                    typeColorClass = 'text-green-700 bg-green-100 dark:text-green-100 dark:bg-green-700';
                } else if (movementTypeLower.includes('ขายออก') || movementTypeLower.includes('จ่ายออก')) {
                    typeColorClass = 'text-red-700 bg-red-100 dark:text-red-100 dark:bg-red-700';
                } else if (movementTypeLower.includes('ปรับปรุง') || movementTypeLower.includes('ย้าย')) {
                    typeColorClass = 'text-blue-700 bg-blue-100 dark:text-blue-100 dark:bg-blue-600';
                }
                typeSpan.className = `px-2 py-1 text-xs font-medium rounded-full ${typeColorClass}`;
                typeCell.appendChild(typeSpan);

                const qtyCell = row.insertCell();
                qtyCell.className = 'text-right';
                qtyCell.textContent = entry.QuantityChange !== null ? parseFloat(entry.QuantityChange).toLocaleString('th-TH') : '-';
                const balanceCell = row.insertCell();
                balanceCell.className = 'text-right';
                balanceCell.textContent = entry.BalanceAfter !== null ? parseFloat(entry.BalanceAfter).toLocaleString('th-TH') : 'N/A';
                row.insertCell().textContent = entry.Reference || '-';
            });
        }
        const startItem = totalItems > 0 ? (currentPageFromApi - 1) * HISTORY_ITEMS_PER_PAGE + 1 : 0;
        const endItem = Math.min(startItem + HISTORY_ITEMS_PER_PAGE - 1, totalItems);
        paginationInfo.innerHTML = `Showing <span class="font-semibold text-slate-900 dark:text-white">${startItem}-${endItem > totalItems ? totalItems : endItem}</span> of <span class="font-semibold text-slate-900 dark:text-white">${totalItems}</span>`;
        renderPaginationControls(paginationControls, currentPageFromApi, Math.ceil(totalItems / HISTORY_ITEMS_PER_PAGE), loadStockHistoryData, currentHistorySearchTerm);
    } else {
        tableBody.innerHTML = `<tr><td colspan="6" class="text-center py-4">ไม่สามารถโหลดข้อมูลประวัติสต็อกได้ (${response.error || 'ไม่ทราบสาเหตุ'})</td></tr>`;
        if (paginationInfo) paginationInfo.textContent = 'Showing 0-0 of 0';
        if(paginationControls) paginationControls.innerHTML = '';
        if (response.error) console.error("Error in loadStockHistoryData:", response.error);
    }
}

// --- User Management Variables and Elements ---
let USER_ITEMS_PER_PAGE_MAIN = parseInt(localStorage.getItem('user_items_per_page_main')) || 10; // For userManagementContent
let currentUserPage = 1;
let currentUserSearchTerm = '';

const editUserModalEl = document.getElementById('editUserModal'); // From new HTML
const editUserFormEl = document.getElementById('editUserForm'); // From new HTML
const closeEditUserModalBtnEl = document.getElementById('closeEditUserModalBtn'); // From new HTML
const cancelEditUserModalBtnEl = document.getElementById('cancelEditUserModalBtn'); // From new HTML

const editUserOriginalUserIDEl = document.getElementById('editUserOriginalUserID'); // From new HTML
const editUserUserIDEl = document.getElementById('editUserUserID');
const editUserUsernameEl = document.getElementById('editUserUsername');
const editUserFullNameEl = document.getElementById('editUserFullName');
const editUserEmailEl = document.getElementById('editUserEmail');
const editUserRoleEl = document.getElementById('editUserRole');
const editUserStatusEl = document.getElementById('editUserStatus');


function initEditUserModal() {
    if (closeEditUserModalBtnEl) closeEditUserModalBtnEl.addEventListener('click', closeEditUserModal);
    if (cancelEditUserModalBtnEl) cancelEditUserModalBtnEl.addEventListener('click', closeEditUserModal);
    if (editUserFormEl) editUserFormEl.addEventListener('submit', handleEditUserFormSubmit);

    if (editUserModalEl) {
        editUserModalEl.addEventListener('click', (event) => {
            if (event.target === editUserModalEl) closeEditUserModal();
        });
    }
    const addUserBtn = document.getElementById('addUserBtn'); // Button in userManagementContent
    if (addUserBtn) {
        addUserBtn.addEventListener('click', () => openEditUserModal(null));
    }
    const addUserBtnDashboard = document.getElementById('add-new-user-btn-dashboard'); // Button in dashboardContent's user table
    if (addUserBtnDashboard) {
        addUserBtnDashboard.addEventListener('click', () => {
            openEditUserModal(null); // Assume it uses the same modal for now
            // If this table is distinct, it might need its own modal or logic
        });
    }
}

function openEditUserModal(user) {
    if (!editUserModalEl) {
        console.error("editUserModalEl not found");
        return;
    }
    const modalTitleEl = document.getElementById('editUserModalTitle');

    if (user) { // Editing
        if (modalTitleEl) modalTitleEl.textContent = 'แก้ไขข้อมูลผู้ใช้';
        if (editUserOriginalUserIDEl) editUserOriginalUserIDEl.value = user.UserID;
        if (editUserUserIDEl) editUserUserIDEl.value = user.UserID || '';
        if (editUserUsernameEl) editUserUsernameEl.value = user.Username || '';
        if (editUserFullNameEl) editUserFullNameEl.value = user.FullName || '';
        if (editUserEmailEl) editUserEmailEl.value = user.Email || '';
        if (editUserRoleEl) editUserRoleEl.value = user.Role || 'User';
        if (editUserStatusEl) editUserStatusEl.value = user.Status || 'Active';
        if (editUserUserIDEl) editUserUserIDEl.disabled = true;
    } else { // Adding new
        if (modalTitleEl) modalTitleEl.textContent = 'เพิ่มผู้ใช้ใหม่';
        if (editUserFormEl) editUserFormEl.reset();
        if (editUserOriginalUserIDEl) editUserOriginalUserIDEl.value = '';
        if (editUserUserIDEl) {
            editUserUserIDEl.value = '';
            // Decide if UserID is editable for new users or server-generated
            // For now, assume it's not directly editable in this form when adding.
            // If user needs to input it, ensure the field is enabled.
            editUserUserIDEl.disabled = true; // Or false if user needs to input it
        }
    }
    editUserModalEl.style.display = 'flex';
    document.body.classList.add('modal-open');
}

function closeEditUserModal() {
    if (!editUserModalEl) return;
    document.body.classList.remove('modal-open');
    editUserModalEl.style.display = 'none';
    if (editUserFormEl) editUserFormEl.reset();
}

async function handleEditUserFormSubmit(event) {
    event.preventDefault();
    if (!editUserFormEl) return;

    const originalUserID = editUserOriginalUserIDEl.value;
    const userData = {
        Username: editUserUsernameEl.value,
        FullName: editUserFullNameEl.value,
        Email: editUserEmailEl.value,
        Role: editUserRoleEl.value,
        Status: editUserStatusEl.value,
    };
    // If UserID field is enabled and it's for a new user, include it
    if (!originalUserID && editUserUserIDEl && !editUserUserIDEl.disabled && editUserUserIDEl.value) {
        userData.UserID = editUserUserIDEl.value;
    }


    const submitButton = editUserFormEl.querySelector('button[type="submit"]');
    const originalButtonText = submitButton.textContent; // Use textContent for button text
    submitButton.disabled = true;
    submitButton.innerHTML = `<svg aria-hidden="true" role="status" class="inline w-4 h-4 mr-2 text-white animate-spin" viewBox="0 0 100 101" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M100 50.5908C100 78.2051 77.6142 100.591 50 100.591C22.3858 100.591 0 78.2051 0 50.5908C0 22.9766 22.3858 0.59082 50 0.59082C77.6142 0.59082 100 22.9766 100 50.5908ZM9.08144 50.5908C9.08144 73.1895 27.4013 91.5094 50 91.5094C72.5987 91.5094 90.9186 73.1895 90.9186 50.5908C90.9186 27.9921 72.5987 9.67226 50 9.67226C27.4013 9.67226 9.08144 27.9921 9.08144 50.5908Z" fill="#E5E7EB"/><path d="M93.9676 39.0409C96.393 38.4038 97.8624 35.9116 97.0079 33.5539C95.2932 28.8227 92.871 24.3692 89.8167 20.348C85.8452 15.1192 80.8826 10.7238 75.2124 7.41289C69.5422 4.10194 63.2754 1.94025 56.7698 1.05124C51.7666 0.367541 46.6976 0.446843 41.7345 1.27873C39.2613 1.69328 37.813 4.19778 38.4501 6.62326C39.0873 9.04874 41.5694 10.4717 44.0505 10.1071C47.8511 9.54855 51.7191 9.52689 55.5402 10.0492C60.8642 10.7766 65.9928 12.5457 70.6331 15.2552C75.2735 17.9648 79.3347 21.5619 82.5849 25.841C84.9175 28.9121 86.7997 32.2913 88.1811 35.8758C89.083 38.2158 91.5424 39.6781 93.9676 39.0409Z" fill="currentColor"/></svg> กำลังบันทึก...`;


    let response;
    let endpoint;
    let method;

    if (originalUserID) {
        endpoint = `/users/${originalUserID}`;
        method = 'PUT';
    } else {
        endpoint = `/users`;
        method = 'POST';
    }

    response = await fetchData(endpoint, method, userData);
    submitButton.disabled = false;
    submitButton.textContent = originalButtonText; // Restore original text

    if (response.success) {
        const actionText = originalUserID ? 'อัปเดตข้อมูลผู้ใช้สำเร็จ!' : 'เพิ่มผู้ใช้ใหม่สำเร็จ!';
        showToast(actionText, 'success');
        closeEditUserModal();
        await loadUserData(originalUserID ? currentUserPage : 1, currentUserSearchTerm);
    } else {
        showToast(`เกิดข้อผิดพลาด: ${response.error || 'ไม่สามารถบันทึกข้อมูลผู้ใช้ได้'}`, 'error');
    }
}

async function handleDeleteUser(userId, username) {
    if (!confirm(`คุณแน่ใจหรือไม่ว่าต้องการลบผู้ใช้ "${username}" (ID: ${userId})?\nการกระทำนี้ไม่สามารถย้อนกลับได้`)) {
        return;
    }
    const response = await fetchData(`/users/${userId}`, 'DELETE');
    if (response.success) {
        showToast(`ผู้ใช้ "${username}" ถูกลบแล้ว`, 'success');
        const userTableBodyMain = document.getElementById('user-table-body-main');
        if (userTableBodyMain && userTableBodyMain.rows.length === 0 && currentUserPage > 1) {
            await loadUserData(currentUserPage - 1, currentUserSearchTerm);
        } else {
            await loadUserData(currentUserPage, currentUserSearchTerm);
        }
    } else {
        showToast(`เกิดข้อผิดพลาดในการลบผู้ใช้: ${response.error || 'ไม่สามารถลบผู้ใช้ได้'}`, 'error');
    }
}

async function loadUserData(page = 1, searchTerm = '') {
    currentUserPage = page;
    currentUserSearchTerm = searchTerm;

    const tableBody = document.getElementById('user-table-body-main');
    const paginationInfo = document.getElementById('user-pagination-info-main');
    const paginationControls = document.getElementById('user-pagination-controls-main');
    const userEntriesSelect = document.getElementById('user-entries-select-main');

    if (userEntriesSelect) { // Update items per page from the correct select
        USER_ITEMS_PER_PAGE_MAIN = parseInt(userEntriesSelect.value);
    }

    const endpoint = `/users?page=${page}&per_page=${USER_ITEMS_PER_PAGE_MAIN}&search=${encodeURIComponent(searchTerm)}`;
    const loadingRow = `<tr><td colspan="8" class="text-center py-10"><div class="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-500 border-r-transparent motion-reduce:animate-[spin_1.5s_linear_infinite]" role="status"><span class="!absolute !-m-px !h-px !w-px !overflow-hidden !whitespace-nowrap !border-0 !p-0 ![clip:rect(0,0,0,0)]">Loading...</span></div></td></tr>`;

    if (!tableBody || !paginationInfo || !paginationControls) {
        console.error("User table elements for 'userManagementContent' not found!");
        return;
    }
    tableBody.innerHTML = loadingRow;

    const response = await fetchData(endpoint);

    if (response.success && response.data && Array.isArray(response.data.data)) {
        const users = response.data.data;
        const totalItems = response.data.total;
        const currentPageFromApi = response.data.page;
        tableBody.innerHTML = '';

        if (users.length === 0) {
            const message = searchTerm ? 'ไม่พบข้อมูลผู้ใช้ที่ตรงกับการค้นหา' : 'ไม่พบข้อมูลผู้ใช้';
            tableBody.innerHTML = `<tr><td colspan="8" class="text-center py-4">${message}</td></tr>`;
        } else {
            users.forEach(user => {
                const row = tableBody.insertRow();
                row.className = tableBody.rows.length % 2 === 0 ?
                    'bg-slate-50 dark:bg-slate-700 hover:bg-slate-100 dark:hover:bg-slate-600' :
                    'bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-600';

                row.insertCell().textContent = user.UserID || '-';
                row.insertCell().textContent = user.Username || '-';
                row.insertCell().textContent = user.FullName || '-';
                row.insertCell().textContent = user.Email || '-';
                row.insertCell().textContent = user.Role || 'User';

                const statusCell = row.insertCell();
                const statusSpan = document.createElement('span');
                statusSpan.textContent = user.Status || 'N/A';
                statusSpan.className = `px-2 py-1 text-xs font-medium rounded-full ${
                    user.Status === 'Active' ? 'text-green-700 bg-green-100 dark:text-green-100 dark:bg-green-700' :
                    user.Status === 'Inactive' ? 'text-yellow-700 bg-yellow-100 dark:text-yellow-100 dark:bg-yellow-600' :
                    user.Status === 'Suspended' ? 'text-red-700 bg-red-100 dark:text-red-100 dark:bg-red-700' :
                    'text-slate-700 bg-slate-100 dark:text-slate-200 dark:bg-slate-600'
                }`;
                statusCell.appendChild(statusSpan);
                row.insertCell().textContent = user.LastLogin ? new Date(user.LastLogin).toLocaleString('th-TH', {dateStyle:'short', timeStyle:'short'}) : '-';

                const actionsCell = row.insertCell();
                actionsCell.className = 'px-6 py-3 text-center space-x-2 whitespace-nowrap';

                const editButton = document.createElement('button');
                editButton.type = 'button';
                editButton.title = "แก้ไขผู้ใช้";
                editButton.className = "text-indigo-600 hover:text-indigo-900 dark:text-indigo-400 dark:hover:text-indigo-300 focus:outline-none";
                editButton.innerHTML = `<svg class="w-5 h-5 inline-block" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"></path></svg>`;
                editButton.onclick = () => openEditUserModal(user);
                actionsCell.appendChild(editButton);

                const deleteButton = document.createElement('button');
                deleteButton.type = 'button';
                deleteButton.title = "ลบผู้ใช้";
                deleteButton.className = "text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300 focus:outline-none";
                deleteButton.innerHTML = `<svg class="w-5 h-5 inline-block" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>`;
                deleteButton.onclick = () => handleDeleteUser(user.UserID, user.Username);
                actionsCell.appendChild(deleteButton);
            });
        }
        const startItem = totalItems > 0 ? (currentPageFromApi - 1) * USER_ITEMS_PER_PAGE_MAIN + 1 : 0;
        const endItem = Math.min(startItem + USER_ITEMS_PER_PAGE_MAIN - 1, totalItems);
        paginationInfo.innerHTML = `Showing <span class="font-semibold text-slate-900 dark:text-white">${startItem}-${endItem > totalItems ? totalItems : endItem}</span> of <span class="font-semibold text-slate-900 dark:text-white">${totalItems}</span>`;
        renderPaginationControls(paginationControls, currentPageFromApi, Math.ceil(totalItems / USER_ITEMS_PER_PAGE_MAIN), loadUserData, currentUserSearchTerm);
    } else {
        tableBody.innerHTML = `<tr><td colspan="8" class="text-center py-4">ไม่สามารถโหลดข้อมูลผู้ใช้ได้ (${response.error || 'ไม่ทราบสาเหตุ'})</td></tr>`;
        if (paginationInfo) paginationInfo.textContent = 'Showing 0-0 of 0';
        if(paginationControls) paginationControls.innerHTML = '';
        if (response.error) console.error("Error in loadUserData:", response.error);
    }
}

function renderPaginationControls(controlsContainer, currentPage, totalPages, loadDataFunction, currentSearchTerm = '') {
    controlsContainer.innerHTML = '';
    if (totalPages <= 1) return;
    const maxPagesToShow = 5;
    let startPage, endPage;
    if (totalPages <= maxPagesToShow) {
        startPage = 1;
        endPage = totalPages;
    } else {
        const maxPagesBeforeCurrentPage = Math.floor(maxPagesToShow / 2);
        const maxPagesAfterCurrentPage = Math.ceil(maxPagesToShow / 2) - 1;
        if (currentPage <= maxPagesBeforeCurrentPage) {
            startPage = 1;
            endPage = maxPagesToShow;
        } else if (currentPage + maxPagesAfterCurrentPage >= totalPages) {
            startPage = totalPages - maxPagesToShow + 1;
            endPage = totalPages;
        } else {
            startPage = currentPage - maxPagesBeforeCurrentPage;
            endPage = currentPage + maxPagesAfterCurrentPage;
        }
    }
    const prevLi = document.createElement('li');
    const prevButton = document.createElement('button');
    prevButton.textContent = 'Previous';
    prevButton.className = "flex items-center justify-center px-3 h-8 ml-0 leading-tight text-slate-500 bg-white border border-slate-300 rounded-l-lg hover:bg-slate-100 hover:text-slate-700 disabled:opacity-50 disabled:cursor-not-allowed dark:bg-slate-800 dark:border-slate-700 dark:text-slate-400 dark:hover:bg-slate-700 dark:hover:text-white";
    if (currentPage === 1) prevButton.disabled = true;
    prevButton.onclick = () => loadDataFunction(currentPage - 1, currentSearchTerm);
    prevLi.appendChild(prevButton);
    controlsContainer.appendChild(prevLi);
    if (startPage > 1) {
        const firstPageLi = document.createElement('li');
        const firstPageLink = document.createElement('a');
        firstPageLink.href = '#';
        firstPageLink.textContent = '1';
        firstPageLink.className = "flex items-center justify-center px-3 h-8 leading-tight text-slate-500 bg-white border border-slate-300 hover:bg-slate-100 hover:text-slate-700 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-400 dark:hover:bg-slate-700 dark:hover:text-white";
        firstPageLink.onclick = (e) => { e.preventDefault(); loadDataFunction(1, currentSearchTerm); };
        firstPageLi.appendChild(firstPageLink);
        controlsContainer.appendChild(firstPageLi);
        if (startPage > 2) {
            const ellipsisLi = document.createElement('li');
            ellipsisLi.innerHTML = `<span class="flex items-center justify-center px-3 h-8 leading-tight text-slate-500 bg-white border border-slate-300 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-400">...</span>`;
            controlsContainer.appendChild(ellipsisLi);
        }
    }
    for (let i = startPage; i <= endPage; i++) {
        const pageLi = document.createElement('li');
        const pageLink = document.createElement(i === currentPage ? 'span' : 'a');
        pageLink.href = i === currentPage ? undefined : '#';
        pageLink.textContent = i;
        pageLink.className = `flex items-center justify-center px-3 h-8 leading-tight border border-slate-300 dark:border-slate-700 `;
        if (i === currentPage) {
            pageLink.className += 'text-blue-600 bg-blue-50 hover:bg-blue-100 hover:text-blue-700 z-10 dark:bg-slate-700 dark:text-blue-400';
            pageLink.setAttribute('aria-current', 'page');
        } else {
            pageLink.className += 'text-slate-500 bg-white hover:bg-slate-100 hover:text-slate-700 dark:bg-slate-800 dark:text-slate-400 dark:hover:bg-slate-700 dark:hover:text-white';
            pageLink.onclick = (e) => { e.preventDefault(); loadDataFunction(i, currentSearchTerm); };
        }
        pageLi.appendChild(pageLink);
        controlsContainer.appendChild(pageLi);
    }
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            const ellipsisLi = document.createElement('li');
            ellipsisLi.innerHTML = `<span class="flex items-center justify-center px-3 h-8 leading-tight text-slate-500 bg-white border border-slate-300 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-400">...</span>`;
            controlsContainer.appendChild(ellipsisLi);
        }
        const lastPageLi = document.createElement('li');
        const lastPageLink = document.createElement('a');
        lastPageLink.href = '#';
        lastPageLink.textContent = totalPages;
        lastPageLink.className = "flex items-center justify-center px-3 h-8 leading-tight text-slate-500 bg-white border border-slate-300 hover:bg-slate-100 hover:text-slate-700 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-400 dark:hover:bg-slate-700 dark:hover:text-white";
        lastPageLink.onclick = (e) => { e.preventDefault(); loadDataFunction(totalPages, currentSearchTerm); };
        lastPageLi.appendChild(lastPageLink);
        controlsContainer.appendChild(lastPageLi);
    }
    const nextLi = document.createElement('li');
    const nextButton = document.createElement('button');
    nextButton.textContent = 'Next';
    nextButton.className = "flex items-center justify-center px-3 h-8 leading-tight text-slate-500 bg-white border border-slate-300 rounded-r-lg hover:bg-slate-100 hover:text-slate-700 disabled:opacity-50 disabled:cursor-not-allowed dark:bg-slate-800 dark:border-slate-700 dark:text-slate-400 dark:hover:bg-slate-700 dark:hover:text-white";
    if (currentPage === totalPages || totalPages === 0) nextButton.disabled = true;
    nextButton.onclick = () => loadDataFunction(currentPage + 1, currentSearchTerm);
    nextLi.appendChild(nextButton);
    controlsContainer.appendChild(nextLi);
}

// >>> ADDED/MODIFIED: Variables for Database Explorer <<<
//------------------------------------------------------------------
let currentDbExplorerTable = '';
let currentDbExplorerPage = 1;
const DB_EXPLORER_ITEMS_PER_PAGE = 20; // หรือค่าที่คุณต้องการ
//------------------------------------------------------------------

// >>> ADDED/MODIFIED: Functions for Database Explorer <<<
//------------------------------------------------------------------
async function initDatabaseExplorerPage() {
    console.log("Initializing Database Explorer Page");
    const tableSelect = document.getElementById('db-table-select');
    if (!tableSelect) {
        console.error("Element with ID 'db-table-select' not found for Database Explorer.");
        return;
    }
    await loadDatabaseTablesDropdown(); 
    
    // Clone and replace to remove old listeners, then add new one
    const newSelect = tableSelect.cloneNode(false); // Clone only the select element itself, not options yet
    while (tableSelect.firstChild) { // Move existing options to the new clone
        newSelect.appendChild(tableSelect.firstChild);
    }
    tableSelect.parentNode.replaceChild(newSelect, tableSelect); // Replace old select with the new one

    newSelect.addEventListener('change', (event) => {
        const selectedTable = event.target.value;
        const displayNameElement = document.getElementById('selected-table-name-display');
        if (displayNameElement) {
            displayNameElement.textContent = selectedTable ? `Data for table: ${selectedTable}` : '';
        }

        if (selectedTable) {
            loadDynamicTableData(selectedTable, 1);
        } else {
            const dynamicTableHead = document.querySelector('#dynamic-db-table thead');
            const dynamicTableBody = document.querySelector('#dynamic-db-table tbody');
            const paginationInfo = document.getElementById('dynamic-db-pagination-info');
            const paginationControls = document.getElementById('dynamic-db-pagination-controls');
            if (dynamicTableHead) dynamicTableHead.innerHTML = '';
            if (dynamicTableBody) dynamicTableBody.innerHTML = '<tr><td class="p-4 text-center text-slate-500 dark:text-slate-400" colspan="1">Please select a table to view its data.</td></tr>';
            if (paginationInfo) paginationInfo.textContent = '';
            if (paginationControls) paginationControls.innerHTML = '';
        }
    });

    const initialSelectedTable = newSelect.value; // Use newSelect here
    const initialDisplayNameElement = document.getElementById('selected-table-name-display');
    if (initialDisplayNameElement) {
            initialDisplayNameElement.textContent = initialSelectedTable ? `Data for table: ${initialSelectedTable}` : '';
    }
    if (initialSelectedTable) {
        loadDynamicTableData(initialSelectedTable, 1);
    } else {
        const dynamicTableBody = document.querySelector('#dynamic-db-table tbody');
        if (dynamicTableBody) dynamicTableBody.innerHTML = '<tr><td class="p-4 text-center text-slate-500 dark:text-slate-400" colspan="1">Please select a table to view its data.</td></tr>';
    }
}
async function setAsDashboardSource(tableName) {
    if (!tableName) {
        showToast('ไม่พบชื่อตารางที่ต้องการตั้งค่า', 'error');
        return;
    }

    if (!confirm(`คุณแน่ใจหรือไม่ว่าต้องการตั้งค่าตาราง "${tableName}" เป็นแหล่งข้อมูลหลักของ Dashboard ทั้งหมด?\nข้อมูล KPI, กราฟ, รายการสินค้า, และประวัติสต็อก จะถูกคำนวณใหม่จากตารางนี้ (หากตารางนี้มีข้อมูลที่เข้ากันได้)`)) {
        return;
    }

    showToast(`กำลังตั้งค่าตาราง "${tableName}" เป็นแหล่งข้อมูลหลัก... โปรดรอสักครู่`, 'info');
    const response = await fetchData('/dashboard/set-source-table', 'POST', { table_name: tableName });

    if (response.success && response.data) {
        showToast(response.data.message || `ตั้งค่าตาราง "${tableName}" เป็นข้อมูลหลักสำเร็จแล้ว! กำลังรีเฟรช Dashboard...`, 'success');
        
        // หลังจาก Backend อัปเดตแหล่งข้อมูลแล้ว ให้ Frontend โหลดข้อมูล Dashboard ใหม่ทั้งหมด
        // 1. รีเฟรชข้อมูล KPI และ Charts ของ Dashboard หลัก
        if (typeof updateKpiData === 'function') await updateKpiData();
        if (typeof renderCharts === 'function') await renderCharts();
        
        // 2. (สำคัญมาก) รีเฟรชข้อมูลหน้า Products และ Stock History
        //    คำเตือน: ถ้าโครงสร้างตารางใหม่ไม่เข้ากันกับที่หน้า Products/Stock History คาดหวัง ส่วนนี้อาจจะแสดงผลผิดพลาดหรือว่างเปล่า
        if (typeof loadProductData === 'function') {
            console.log("Attempting to reload Product Data based on new source table...");
            // Reset search term and page for product data as context changed
            currentProductSearchTerm = ''; 
            currentProductPage = 1;
            await loadProductData(currentProductPage, currentProductSearchTerm);
        }
        if (typeof loadStockHistoryData === 'function') {
            console.log("Attempting to reload Stock History Data based on new source table...");
            // Reset search term and page for stock history
            currentHistorySearchTerm = '';
            currentHistoryPage = 1;
            await loadStockHistoryData(currentHistoryPage, currentHistorySearchTerm);
        }
        // (อาจจะต้อง reload User data ด้วยถ้ามันเกี่ยวข้อง)

        // 3. นำทางผู้ใช้กลับไปที่หน้า Dashboard หลัก (หรือให้ Dashboard รีเฟรชตัวเองถ้าอยู่หน้านั้นแล้ว)
        // ใช้ Custom Event เพื่อให้ SPA navigation จัดการอย่างถูกต้อง
        const pageChangeEvent = new CustomEvent('pageChangeRequested', { detail: { pageId: 'dashboardContent' } });
        document.dispatchEvent(pageChangeEvent);
        // หรือถ้า showPage สามารถเรียกได้โดยตรงและจัดการการ re-initialization ของ dashboardContent ได้ถูกต้อง
        // showPage('dashboardContent'); 
        
        updateLastUpdated(); // อัปเดตเวลา "ข้อมูลล่าสุด"

    } else {
        showToast(`เกิดข้อผิดพลาดในการตั้งค่า: ${response.error || 'ไม่สามารถตั้งค่าตารางหลักได้'}`, 'error');
    }
}
async function loadDatabaseTablesDropdown() {
    const tableSelect = document.getElementById('db-table-select');
    if (!tableSelect) {
        console.error("Dropdown 'db-table-select' not found.");
        return;
    }
    const originalValue = tableSelect.value;

    const response = await fetchData('/database/tables');
    if (response.success && Array.isArray(response.data)) {
        const placeholderOptionHTML = '<option value="">-- กรุณาเลือกตาราง --</option>';
        tableSelect.innerHTML = placeholderOptionHTML; // Reset with placeholder

        response.data.forEach(tableName => {
            const option = document.createElement('option');
            option.value = tableName;
            option.textContent = tableName;
            tableSelect.appendChild(option);
        });
        
        // Try to restore previous selection if it exists in the new list
        if (response.data.includes(originalValue)) {
            tableSelect.value = originalValue;
        } else {
            tableSelect.value = ""; // Default to placeholder if old selection is invalid
        }
    } else {
        showToast('Error loading table list: ' + (response.error || 'Unknown error'), 'error');
    }
}

async function loadDynamicTableData(tableName, page = 1) {
    if (!tableName) {
        console.log("loadDynamicTableData: No table selected.");
        // Clear UI elements if no table is selected
        const dynamicTableHead = document.querySelector('#dynamic-db-table thead');
        const dynamicTableBody = document.querySelector('#dynamic-db-table tbody');
        const paginationInfo = document.getElementById('dynamic-db-pagination-info');
        const paginationControls = document.getElementById('dynamic-db-pagination-controls');
        const selectedTableNameDisplay = document.getElementById('selected-table-name-display');
        const controlsContainer = document.getElementById('dynamic-table-header-controls');


        if (selectedTableNameDisplay) selectedTableNameDisplay.textContent = '';
        if (dynamicTableHead) dynamicTableHead.innerHTML = '';
        if (dynamicTableBody) dynamicTableBody.innerHTML = '<tr><td class="p-4 text-center text-slate-500 dark:text-slate-400" colspan="1">Please select a table to view its data.</td></tr>';
        if (paginationInfo) paginationInfo.textContent = '';
        if (paginationControls) paginationControls.innerHTML = '';
        if (controlsContainer) { // Remove "Set as Source" button if it exists
            const oldButton = controlsContainer.querySelector('.set-dashboard-source-btn');
            if (oldButton) oldButton.remove();
        }
        return;
    }

    console.log(`loadDynamicTableData: Called for table "${tableName}", page ${page}`);

    const dynamicTableHead = document.querySelector('#dynamic-db-table thead');
    const dynamicTableBody = document.querySelector('#dynamic-db-table tbody');
    const paginationInfo = document.getElementById('dynamic-db-pagination-info');
    const paginationControls = document.getElementById('dynamic-db-pagination-controls');
    const selectedTableNameDisplay = document.getElementById('selected-table-name-display');
    const controlsContainer = document.getElementById('dynamic-table-header-controls'); // Container for H3 and button

    if (!dynamicTableHead || !dynamicTableBody || !paginationInfo || !paginationControls || !selectedTableNameDisplay || !controlsContainer) {
        console.error("One or more dynamic DB table elements are missing from the DOM!");
        showToast("เกิดข้อผิดพลาด: ไม่พบองค์ประกอบสำหรับแสดงตาราง", "error");
        return;
    }

    // --- Display Loading State ---
    selectedTableNameDisplay.textContent = `Loading data for table: ${tableName}...`;
    dynamicTableHead.innerHTML = ''; 
    dynamicTableBody.innerHTML = `<tr><td colspan="99" class="text-center py-10"><div class="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-500 border-r-transparent motion-reduce:animate-[spin_1.5s_linear_infinite]" role="status"><span class="sr-only">Loading...</span></div></td></tr>`;
    paginationInfo.textContent = 'Loading pagination...';
    paginationControls.innerHTML = '';
    // Remove old "Set as Source" button during loading
    const oldBtnDuringLoad = controlsContainer.querySelector('.set-dashboard-source-btn');
    if (oldBtnDuringLoad) oldBtnDuringLoad.remove();

    const endpoint = `/database/table/${tableName}?page=${page}&per_page=${DB_EXPLORER_ITEMS_PER_PAGE}`;
    const response = await fetchData(endpoint);
    console.log(`loadDynamicTableData: Response from API for table "${tableName}":`, response);

    if (response.success && response.data) {
        const { data: rows, columns, total, page: currentPageFromApi, per_page, table_name: actualTableName } = response.data;
        console.log("loadDynamicTableData: API call successful. Actual table name:", actualTableName);
        
        selectedTableNameDisplay.textContent = `Data for table: ${actualTableName}`;
        let colCount = 1; // Default colspan for messages if no columns

        // --- Create Table Header (thead) ---
        dynamicTableHead.innerHTML = ''; // Clear previous header
        if (columns && columns.length > 0) {
            colCount = columns.length;
            const headerRow = dynamicTableHead.insertRow();
            columns.forEach(colName => {
                const th = document.createElement('th');
                th.scope = 'col';
                th.className = 'px-4 sm:px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-300 uppercase tracking-wider';
                th.textContent = colName;
                headerRow.appendChild(th);
            });
        } else if (rows && rows.length > 0) { // Fallback if 'columns' array is missing but data rows exist
            const firstRowColumns = Object.keys(rows[0]);
            colCount = firstRowColumns.length;
            const headerRow = dynamicTableHead.insertRow();
            firstRowColumns.forEach(colName => {
                const th = document.createElement('th');
                th.scope = 'col';
                th.className = 'px-4 sm:px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-300 uppercase tracking-wider';
                th.textContent = colName;
                headerRow.appendChild(th);
            });
        } else {
            // No columns and no rows, or columns array is empty
            dynamicTableHead.innerHTML = '<tr><th class="px-4 sm:px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-300">Info</th></tr>'; // Minimal header
        }

        // --- Populate Table Body (tbody) ---
        dynamicTableBody.innerHTML = ''; 
        if (!rows || rows.length === 0) {
            dynamicTableBody.innerHTML = `<tr><td colspan="${colCount}" class="text-center p-4 text-slate-500 dark:text-slate-400">No data found in table '${actualTableName}'.</td></tr>`;
        } else {
            const displayColumns = columns && columns.length > 0 ? columns : Object.keys(rows[0]); 
            rows.forEach(rowData => {
                const tr = dynamicTableBody.insertRow();
                tr.className = dynamicTableBody.rows.length % 2 === 0 ? 'bg-slate-50 dark:bg-slate-700/50 hover:bg-slate-100 dark:hover:bg-slate-600/50' : 'bg-white dark:bg-slate-800/50 hover:bg-slate-50 dark:hover:bg-slate-700/50';
                displayColumns.forEach(colName => {
                    const cell = tr.insertCell();
                    cell.className = 'px-4 sm:px-6 py-3 whitespace-nowrap text-sm text-slate-700 dark:text-slate-200';
                    // Handle null or undefined values gracefully
                    const cellValue = rowData[colName];
                    cell.textContent = cellValue !== null && cellValue !== undefined ? String(cellValue) : '-';
                });
            });
        }

        // --- Create "Set as Main Dashboard Source" Button ---
        // Ensure old button is removed before adding new one, and only if actualTableName is valid
        const oldButton = controlsContainer.querySelector('.set-dashboard-source-btn');
        if (oldButton) {
            oldButton.remove();
        }
        if (actualTableName) {
            const setSourceButton = document.createElement('button');
            setSourceButton.textContent = `ใช้ตาราง "${actualTableName}" เป็นข้อมูลหลัก Dashboard`;
            setSourceButton.className = 'ml-auto px-3 py-1.5 text-xs font-medium text-white bg-orange-500 hover:bg-orange-600 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500 set-dashboard-source-btn'; // ml-auto to push to the right
            setSourceButton.onclick = () => setAsDashboardSource(actualTableName);
            controlsContainer.appendChild(setSourceButton); // Add button to the controls container
            console.log(`loadDynamicTableData: "Set Source Button" for table "${actualTableName}" added to controls container.`);
        }


        // --- Render Pagination ---
        const startItem = total > 0 ? (currentPageFromApi - 1) * per_page + 1 : 0;
        const endItem = Math.min(startItem + per_page - 1, total);
        paginationInfo.innerHTML = `Showing <span class="font-semibold text-slate-900 dark:text-white">${startItem}-${endItem}</span> of <span class="font-semibold text-slate-900 dark:text-white">${total}</span>`;
        
        renderPaginationControls(
            paginationControls, 
            currentPageFromApi, 
            Math.ceil(total / per_page), 
            (p) => loadDynamicTableData(actualTableName, p), // Pass the actual table name from response
            '' // searchTerm - not used in this version, can be added later
        );

    } else { // API call failed or response.data is missing
        selectedTableNameDisplay.textContent = `Error loading table: ${tableName}`;
        dynamicTableHead.innerHTML = '';
        dynamicTableBody.innerHTML = `<tr><td colspan="1" class="text-center p-4 text-red-500">Error loading data for table '${tableName}': ${response.error || 'Unknown error or no data received'}</td></tr>`;
        paginationInfo.textContent = 'Error loading data';
        paginationControls.innerHTML = '';
        // Ensure button is removed on error too
        const oldButtonOnError = controlsContainer.querySelector('.set-dashboard-source-btn');
        if (oldButtonOnError) oldButtonOnError.remove();
        console.error(`loadDynamicTableData: API call failed or no data for table "${tableName}". Error:`, response.error);
    }
}


let currentActivePageId = 'dashboardContent';

document.addEventListener('DOMContentLoaded', () => {
    const defaultPageId = 'dashboardContent'; 
    currentActivePageId = defaultPageId; // กำหนดค่าเริ่มต้น
    
    // >>> ADDED/MODIFIED: Query pageSections after DOM is fully loaded <<<
    const pageSections = document.querySelectorAll('.page-content-section'); // ย้ายมา query ที่นี่

    updateLastUpdated();
    initEditProductModal();
    initEditUserModal();

    const refreshButton = document.getElementById('refresh-data-btn');
    if (refreshButton) {
        refreshButton.addEventListener('click', () => {
            console.log("Refresh button clicked, current active page:", currentActivePageId);
            showToast('กำลังรีเฟรชข้อมูล...', 'info');
            // updateLastUpdated(); //ย้ายไปเรียกหลังโหลดข้อมูลเสร็จ

            if (currentActivePageId === 'dashboardContent') {
                Promise.all([updateKpiData(), renderCharts()]).then(() => {
                    showToast('ข้อมูล Dashboard อัปเดตแล้ว!', 'success');
                    updateLastUpdated();
                }).catch(error => {
                    console.error("Error during dashboard refresh:", error);
                    showToast('เกิดข้อผิดพลาดในการรีเฟรช Dashboard', 'error');
                });
            } else if (currentActivePageId === 'productContent') {
                loadProductData(currentProductPage, currentProductSearchTerm)
                    .then(() => {
                        showToast('ข้อมูลสินค้าอัปเดตแล้ว!', 'success');
                        updateLastUpdated();
                    })
                    .catch(err => showToast('เกิดข้อผิดพลาดในการรีเฟรชข้อมูลสินค้า', 'error'));
            } else if (currentActivePageId === 'historyContent') {
                loadStockHistoryData(currentHistoryPage, currentHistorySearchTerm)
                    .then(() => {
                        showToast('ประวัติสต็อกอัปเดตแล้ว!', 'success');
                        updateLastUpdated();
                    })
                    .catch(err => showToast('เกิดข้อผิดพลาดในการรีเฟรชประวัติสต็อก', 'error'));
            } else if (currentActivePageId === 'userManagementContent') {
                loadUserData(currentUserPage, currentUserSearchTerm)
                    .then(() => {
                        showToast('ข้อมูลผู้ใช้อัปเดตแล้ว!', 'success');
                        updateLastUpdated();
                    })
                    .catch(err => showToast('เกิดข้อผิดพลาดในการรีเฟรชข้อมูลผู้ใช้', 'error'));
            } else if (currentActivePageId === 'databaseExplorerContent') {
                if (currentDbExplorerTable) { // ตรวจสอบว่ามีตารางกำลังถูกเลือกดูอยู่
                    showToast(`กำลังรีเฟรชข้อมูลตาราง "${currentDbExplorerTable}"...`, 'info');
                    loadDynamicTableData(currentDbExplorerTable, currentDbExplorerPage) // โหลดหน้าปัจจุบันของตารางที่ดูอยู่
                        .then(() => {
                            showToast(`ข้อมูลตาราง "${currentDbExplorerTable}" อัปเดตแล้ว!`, 'success');
                            updateLastUpdated();
                        })
                        .catch(err => {
                            console.error("Error refreshing database explorer table:", err);
                            showToast('เกิดข้อผิดพลาดในการรีเฟรชข้อมูลตาราง', 'error');
                        });
                } else {
                    showToast('กรุณาเลือกตารางใน Database Explorer ก่อนทำการรีเฟรช', 'info');
                    // updateLastUpdated(); // อาจจะไม่ต้อง update ถ้าไม่มีอะไรให้ refresh
                    }
            }
        });
    }

    const productEntriesSelect = document.getElementById('product-entries-select');
    if (productEntriesSelect) {
        const storedProductItemsPerPage = localStorage.getItem('product_items_per_page');
        if (storedProductItemsPerPage) PRODUCT_ITEMS_PER_PAGE = parseInt(storedProductItemsPerPage);
        else PRODUCT_ITEMS_PER_PAGE = 25;
        productEntriesSelect.value = PRODUCT_ITEMS_PER_PAGE;
        productEntriesSelect.addEventListener('change', (e) => {
            PRODUCT_ITEMS_PER_PAGE = parseInt(e.target.value);
            localStorage.setItem('product_items_per_page', PRODUCT_ITEMS_PER_PAGE);
            if (currentActivePageId === 'productContent') loadProductData(1, currentProductSearchTerm);
        });
    }

    const historyEntriesSelect = document.getElementById('stock-history-entries-select');
    if (historyEntriesSelect) {
        const storedHistoryItemsPerPage = localStorage.getItem('history_items_per_page');
        if (storedHistoryItemsPerPage) HISTORY_ITEMS_PER_PAGE = parseInt(storedHistoryItemsPerPage);
        else HISTORY_ITEMS_PER_PAGE = 15;
        historyEntriesSelect.value = HISTORY_ITEMS_PER_PAGE;
        historyEntriesSelect.addEventListener('change', (e) => {
            HISTORY_ITEMS_PER_PAGE = parseInt(e.target.value);
            localStorage.setItem('history_items_per_page', HISTORY_ITEMS_PER_PAGE);
            if (currentActivePageId === 'historyContent') loadStockHistoryData(1, currentHistorySearchTerm);
        });
    }

    const userEntriesSelectMain = document.getElementById('user-entries-select-main');
    if (userEntriesSelectMain) {
        const storedUserItemsPerPage = localStorage.getItem('user_items_per_page_main');
        if (storedUserItemsPerPage) USER_ITEMS_PER_PAGE_MAIN = parseInt(storedUserItemsPerPage); // Correct variable
        else USER_ITEMS_PER_PAGE_MAIN = 10;
        userEntriesSelectMain.value = USER_ITEMS_PER_PAGE_MAIN; // Correct variable
        userEntriesSelectMain.addEventListener('change', (e) => {
            USER_ITEMS_PER_PAGE_MAIN = parseInt(e.target.value); // Correct variable
            localStorage.setItem('user_items_per_page_main', USER_ITEMS_PER_PAGE_MAIN); // Correct variable
            if (currentActivePageId === 'userManagementContent') {
                loadUserData(1, currentUserSearchTerm);
            }
        });
    }

    const userEntriesSelectDashboard = document.getElementById('user-entries-select-dashboard');
    if (userEntriesSelectDashboard) {
        // Placeholder - implement if user table on dashboard is active
    }

    const scrollToTopBtn = document.getElementById('scrollToTopBtn');
    if (scrollToTopBtn) {
        const mainContentArea = document.querySelector('.flex-1.pt-16.overflow-y-auto');
        if (mainContentArea) {
            mainContentArea.onscroll = function() {
                if (mainContentArea.scrollTop > 100) {
                    scrollToTopBtn.classList.remove('opacity-0', 'pointer-events-none');
                    scrollToTopBtn.classList.add('opacity-100');
                } else {
                    scrollToTopBtn.classList.remove('opacity-100');
                    scrollToTopBtn.classList.add('opacity-0', 'pointer-events-none');
                }
            };
            scrollToTopBtn.addEventListener('click', () => {
                mainContentArea.scrollTo({top: 0, behavior: 'smooth'});
            });
        } else {
             window.onscroll = function() {
                if (document.body.scrollTop > 100 || document.documentElement.scrollTop > 100) {
                    scrollToTopBtn.classList.remove('opacity-0', 'pointer-events-none');
                    scrollToTopBtn.classList.add('opacity-100');
                } else {
                    scrollToTopBtn.classList.remove('opacity-100');
                    scrollToTopBtn.classList.add('opacity-0', 'pointer-events-none');
                }
            };
            scrollToTopBtn.addEventListener('click', () => {
                window.scrollTo({top: 0, behavior: 'smooth'});
            });
        }
    }

    // const pageSections = document.querySelectorAll('.page-content-section');

    function showPage(pageId) {
        console.log(`Switching to page: ${pageId}`);
        currentActivePageId = pageId;

        pageSections.forEach(section => {
            section.style.display = (section.id === pageId) ? 'block' : 'none';
        });

        document.dispatchEvent(new CustomEvent('pageChangedByScript', { detail: { pageId: pageId } }));

        if (pageId === 'dashboardContent') {
            updateKpiData();
            renderCharts();
        } else if (pageId === 'productContent') {
            const productSearchInput = document.getElementById('product-table-search');
            if(productSearchInput) productSearchInput.value = currentProductSearchTerm || '';
            loadProductData(currentProductPage, currentProductSearchTerm);
        } else if (pageId === 'historyContent') {
            const historySearchInput = document.getElementById('stock-history-search');
            if(historySearchInput) historySearchInput.value = currentHistorySearchTerm || '';
            loadStockHistoryData(currentHistoryPage, currentHistorySearchTerm);
        } else if (pageId === 'userManagementContent') {
            const userSearchInputMain = document.getElementById('user-table-search-main');
            if(userSearchInputMain) userSearchInputMain.value = currentUserSearchTerm || '';
            loadUserData(currentUserPage, currentUserSearchTerm);
        } else if (pageId === 'databaseExplorerContent') { // >>> ADDED/MODIFIED <<<
            if (typeof initDatabaseExplorerPage === 'function') {
                initDatabaseExplorerPage();
            } else {
                console.error('initDatabaseExplorerPage function is not defined.');
            }
        }
    }

//------------------------------------------------------------------

    document.addEventListener('pageChangeRequested', (event) => {
        const pageId = event.detail.pageId;
        if (pageId && document.getElementById(pageId)) {
            showPage(pageId);
            window.location.hash = pageId;
        } else {
            console.warn(`Page with ID "${pageId}" not found during pageChangeRequested. Defaulting to dashboard.`);
            showPage(defaultPageId); 
            window.location.hash = defaultPageId;
        }
    });

    const productSearchInput = document.getElementById('product-table-search');
    if (productSearchInput) {
        let debounceTimeout;
        productSearchInput.addEventListener('input', (e) => {
            clearTimeout(debounceTimeout);
            debounceTimeout = setTimeout(() => {
                loadProductData(1, e.target.value);
            }, 300);
        });
    }

    const stockHistorySearchInput = document.getElementById('stock-history-search');
    if (stockHistorySearchInput) {
        let debounceTimeout;
        stockHistorySearchInput.addEventListener('input', (e) => {
            clearTimeout(debounceTimeout);
            debounceTimeout = setTimeout(() => {
                loadStockHistoryData(1, e.target.value);
            }, 300);
        });
    }

    const userSearchInputMain = document.getElementById('user-table-search-main');
    if (userSearchInputMain) {
        let debounceTimeout;
        userSearchInputMain.addEventListener('input', (e) => {
            clearTimeout(debounceTimeout);
            debounceTimeout = setTimeout(() => {
                loadUserData(1, e.target.value);
            }, 300);
        });
    }
    
    let initialPageId = defaultPageId; // Use locally defined defaultPageId
    const hash = window.location.hash.substring(1);
    if (hash && document.getElementById(hash)) {
        initialPageId = hash;
    } else {
        window.location.hash = defaultPageId;
    }
    showPage(initialPageId);

    setInterval(updateLastUpdated, 60000);
    setInterval(() => {
        if (currentActivePageId === 'dashboardContent') {
            console.log("Auto-refreshing dashboard KPI and Charts...");
            updateKpiData();
            renderCharts();
        }
    }, 300000);
});