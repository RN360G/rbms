
document.addEventListener("DOMContentLoaded", function () {
    // Restore last active tab from localStorage
    let activeTab = localStorage.getItem("activeTab");
    if (activeTab) {
        let tabTrigger = document.querySelector(`a[href="${activeTab}"]`);
        if (tabTrigger) {
            new bootstrap.Tab(tabTrigger).show();
        }
    }

    // Save active tab whenever user switches
    document.querySelectorAll('a[data-bs-toggle="tab"]').forEach(tab => {
        tab.addEventListener("shown.bs.tab", function (event) {
            localStorage.setItem("activeTab", event.target.getAttribute("href"));
        });
    });
});
