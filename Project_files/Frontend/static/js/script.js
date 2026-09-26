/* =========================================================
   AI RETAIL INVENTORY INTELLIGENCE SYSTEM
   MAIN JAVASCRIPT
   ========================================================= */


/* =========================================================
   1. SIDEBAR TOGGLE
   ========================================================= */

const sidebarToggle = document.getElementById("sidebarToggle");

if (sidebarToggle) {

    sidebarToggle.addEventListener("click", function () {

        if (window.innerWidth <= 768) {

            document.body.classList.toggle(
                "sidebar-mobile-open"
            );

        } else {

            document.body.classList.toggle(
                "sidebar-collapsed"
            );

        }

    });

}


/* =========================================================
   2. THEME TOGGLE
   ========================================================= */

const themeToggle =
    document.getElementById("themeToggle");

const savedTheme =
    localStorage.getItem("theme");


if (savedTheme) {

    document.documentElement.setAttribute(
        "data-theme",
        savedTheme
    );

}


function updateThemeIcon() {

    if (!themeToggle) {
        return;
    }

    const currentTheme =
        document.documentElement.getAttribute(
            "data-theme"
        );

    const icon =
        themeToggle.querySelector("i");

    if (!icon) {
        return;
    }

    if (currentTheme === "dark") {

        icon.className = "bi bi-sun";

        themeToggle.setAttribute(
            "title",
            "Switch to light mode"
        );

    } else {

        icon.className = "bi bi-moon";

        themeToggle.setAttribute(
            "title",
            "Switch to dark mode"
        );

    }

}


updateThemeIcon();


if (themeToggle) {

    themeToggle.addEventListener(
        "click",
        function () {

            const currentTheme =
                document.documentElement.getAttribute(
                    "data-theme"
                );

            const newTheme =
                currentTheme === "dark"
                    ? "light"
                    : "dark";


            document.documentElement.setAttribute(
                "data-theme",
                newTheme
            );


            localStorage.setItem(
                "theme",
                newTheme
            );


            updateThemeIcon();

        }
    );

}


/* =========================================================
   3. PROFILE DROPDOWN
   ========================================================= */

const profileMenuButton =
    document.getElementById(
        "profileMenuButton"
    );

const profileDropdown =
    document.getElementById(
        "profileDropdown"
    );


if (
    profileMenuButton &&
    profileDropdown
) {

    profileMenuButton.addEventListener(
        "click",
        function (event) {

            event.stopPropagation();

            profileDropdown.classList.toggle(
                "show"
            );

        }
    );

}


document.addEventListener(
    "click",
    function (event) {

        if (
            profileDropdown &&
            profileMenuButton &&
            !profileDropdown.contains(event.target) &&
            !profileMenuButton.contains(event.target)
        ) {

            profileDropdown.classList.remove(
                "show"
            );

        }

    }
);


/* =========================================================
   4. CLOSE MOBILE SIDEBAR
   ========================================================= */

document.addEventListener(
    "click",
    function (event) {

        if (
            window.innerWidth <= 768 &&
            document.body.classList.contains(
                "sidebar-mobile-open"
            )
        ) {

            const sidebar =
                document.getElementById(
                    "sidebar"
                );


            if (
                sidebar &&
                sidebarToggle &&
                !sidebar.contains(event.target) &&
                !sidebarToggle.contains(event.target)
            ) {

                document.body.classList.remove(
                    "sidebar-mobile-open"
                );

            }

        }

    }
);


/* =========================================================
   5. WINDOW RESIZE
   ========================================================= */

window.addEventListener(
    "resize",
    function () {

        if (window.innerWidth > 768) {

            document.body.classList.remove(
                "sidebar-mobile-open"
            );

        }

    }
);


/* =========================================================
   6. CURRENT PAGE NAME
   ========================================================= */

function updateCurrentPageName() {

    const pageNameElement =
        document.getElementById(
            "currentPageName"
        );


    if (!pageNameElement) {
        return;
    }


    const path =
        window.location.pathname.toLowerCase();


    let pageName = "Dashboard";


    if (path.includes("inventory")) {

        pageName = "Inventory";

    } else if (
        path.includes("forecast") ||
        path.includes("prediction")
    ) {

        pageName = "AI Forecast";

    } else if (
        path.includes("analytics")
    ) {

        pageName = "Analytics";

    } else if (
        path.includes("report")
    ) {

        pageName = "Reports";

    } else if (
        path.includes("alert")
    ) {

        pageName = "Alerts";

    } else if (
        path.includes("user")
    ) {

        pageName = "Users";

    } else if (
        path.includes("store")
    ) {

        pageName = "Stores";

    } else if (
        path.includes("setting")
    ) {

        pageName = "Settings";

    }


    pageNameElement.textContent =
        pageName;

}


updateCurrentPageName();


/* =========================================================
   7. LOGOUT CONFIRMATION
   ========================================================= */

const logoutLinks =
    document.querySelectorAll(
        ".logout-sidebar-link, .logout-link"
    );


logoutLinks.forEach(
    function (logoutLink) {

        logoutLink.addEventListener(
            "click",
            function (event) {

                const confirmed =
                    confirm(
                        "Are you sure you want to logout?"
                    );


                if (!confirmed) {

                    event.preventDefault();

                }

            }
        );

    }
);


/* =========================================================
   8. CONSOLE MESSAGE
   ========================================================= */

console.log(
    "AI Retail Inventory Intelligence System loaded successfully."
);

// ============================================================
// INVENTORY - FILL SAMPLE DATA
// ============================================================

document.addEventListener("DOMContentLoaded", function () {

    const sampleButton = document.getElementById("fillSampleData");

    if (!sampleButton) {
        return;
    }

    sampleButton.addEventListener("click", function () {

        const store = document.querySelector(
            'select[name="store_id"]'
        );

        const productId = document.querySelector(
            'input[name="product_id"]'
        );

        const category = document.querySelector(
            'select[name="category"]'
        );

        const subcategory = document.querySelector(
            'select[name="subcategory"]'
        );

        const region = document.querySelector(
            'select[name="region"]'
        );

        const inventory = document.querySelector(
            'input[name="inventory_level"]'
        );

        const price = document.querySelector(
            'input[name="price"]'
        );

        const discount = document.querySelector(
            'input[name="discount"]'
        );

        const competitorPricing = document.querySelector(
            'input[name="competitor_pricing"]'
        );

        const weather = document.querySelector(
            'select[name="weather_condition"]'
        );

        const holiday = document.querySelector(
            'select[name="holiday_promotion"]'
        );

        const seasonality = document.querySelector(
            'select[name="seasonality"]'
        );

        const month = document.querySelector(
            'input[name="month"]'
        );

        const day = document.querySelector(
            'input[name="day"]'
        );


        // Fill sample values

        if (store) {
            store.value = "S001";
        }

        if (productId) {
            productId.value = "P0001";
        }

        if (category) {

            category.value = "Electronics";

            // Trigger category change so
            // subcategories are populated

            category.dispatchEvent(
                new Event("change")
            );
        }

        if (subcategory) {

            setTimeout(function () {

                subcategory.value = "Smartphones";

            }, 50);
        }

        if (region) {
            region.value = "South";
        }

        if (inventory) {
            inventory.value = "50";
        }

        if (price) {
            price.value = "500";
        }

        if (discount) {
            discount.value = "10";
        }

        if (competitorPricing) {
            competitorPricing.value = "480";
        }

        if (weather) {
            weather.value = "Sunny";
        }

        if (holiday) {
            holiday.value = "No";
        }

        if (seasonality) {
            seasonality.value = "Summer";
        }

        if (month) {
            month.value = "9";
        }

        if (day) {
            day.value = "5";
        }

    });

});

/* =========================================================
   AI FORECAST COVERAGE BARS
   ========================================================= */

document.addEventListener("DOMContentLoaded", function () {

    const coverageBars =
        document.querySelectorAll(".forecast-coverage-fill");

    coverageBars.forEach(function (bar) {

        let coverage =
            parseFloat(bar.dataset.coverage);

        if (isNaN(coverage)) {
            coverage = 0;
        }

        coverage = Math.max(
            0,
            Math.min(coverage, 100)
        );

        bar.style.width = coverage + "%";

    });

});