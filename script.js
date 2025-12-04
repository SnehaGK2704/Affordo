// static/script.js

function $(sel) { return document.querySelector(sel); }
function $all(sel) { return Array.from(document.querySelectorAll(sel)); }

// =========================================
// CATEGORY SELECTION (NEW FEATURE)
// =========================================
let selectedCategory = "all";  // default category

// Detect clicks on category filter buttons
$all(".filter-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        // Remove active class from all
        $all(".filter-btn").forEach(b => b.classList.remove("active"));

        // Add active to clicked
        btn.classList.add("active");

        // Read text inside button
        const cat = btn.textContent.trim().toLowerCase();

        if (cat.includes("fashion")) selectedCategory = "fashion";
        else if (cat.includes("electronics")) selectedCategory = "electronics";
        else if (cat.includes("sports")) selectedCategory = "sports";
        else selectedCategory = "all";  // default

        console.log("Selected category:", selectedCategory);
    });
});


// =========================================
// SEARCH TAB SWITCHING
// =========================================
function switchSearchTab(tab) {
    $all('.search-tab').forEach(b => b.classList.remove('active'));
    $all('.search-tab-content').forEach(c => c.classList.remove('active'));

    $all('.search-tab').forEach(btn => {
        if (btn.textContent.toLowerCase().includes(tab)) {
            btn.classList.add('active');
        }
    });

    const id = 'search' + tab.charAt(0).toUpperCase() + tab.slice(1);
    const el = document.getElementById(id);
    if (el) el.classList.add('active');
}


// =========================================
// SEARCH BY PRODUCT NAME
// =========================================
function searchProducts() {
    const q = document.getElementById('searchInput').value.trim();
    if (!q) return alert('Please enter a search term');

    window.location.href = '/results?query=' + encodeURIComponent(q) + '&cat=' + selectedCategory;
}


// =========================================
// SEARCH BY PRODUCT CODE
// =========================================
function searchByProductCode() {
    const code = document.getElementById('productCodeInput').value.trim();
    if (!code) return alert('Enter product code');

    window.location.href = '/results?query=' + encodeURIComponent(code) + '&cat=' + selectedCategory;
}


// =========================================
// SEARCH BY PRODUCT LINK
// =========================================
function searchByProductLink() {
    const link = document.getElementById('productLinkInput').value.trim();
    if (!link) return alert("Paste a product link");

    window.location.href = '/results?query=' + encodeURIComponent(link) + '&cat=' + selectedCategory;
}


// =========================================
// MODAL
// =========================================
function openModal(html) {
    const modal = document.getElementById('productModal');
    if (!modal) return;
    document.getElementById('modalBody').innerHTML = html;
    modal.style.display = 'block';
}

function closeModal() {
    const modal = document.getElementById('productModal');
    if (!modal) return;
    modal.style.display = 'none';
}

window.closeModal = closeModal;
window.searchProducts = searchProducts;
window.searchByProductCode = searchByProductCode;
window.searchByProductLink = searchByProductLink;


// Close modal on outside click
window.onclick = function (event) {
    const modal = document.getElementById('productModal');
    if (modal && event.target === modal) modal.style.display = 'none';
};
