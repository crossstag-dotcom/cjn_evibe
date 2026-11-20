

document.addEventListener("DOMContentLoaded", function () {

    const paymentMethod = document.getElementById("payment_method");
    const codChargeValue = document.getElementById("cod-charge-value");
    const codLabel = document.getElementById("cod-label");

    const paymentNote = document.getElementById("payment-note");

    const payToday = document.getElementById("pay-today");

    const payLater = document.getElementById("pay-later");
    const totalPayable = document.getElementById("total-payable");

    const totalSavings = document.getElementById("total-savings");
    const savingsBreakdown = document.getElementById("savings-breakdown");

    const codCharge = Number("{{ cod_charge }}");
    const totalWithCOD = Number("{{ final_total }}");
    const totalWithoutCOD = totalWithCOD - codCharge;

    const productSavings = Number("{{ total_savings }}");
    const codPayNow = Number("{{ cod_pay_now }}");
    const codPayLater = Number("{{ cod_pay_later }}");
    const onlinePayNow = Number("{{ online_pay_now }}");

    // Validation Inputs
    const customerName = document.getElementById("customer_name");
    const phone = document.getElementById("phone");
    const email = document.getElementById("email");
    const city = document.getElementById("city");
    const pincode = document.getElementById("pincode");

    // Validation Messages
    const customerNameMessage = document.getElementById("customer_name_message");
    const phoneMessage = document.getElementById("phone_message");
    const emailMessage = document.getElementById("email_message");
    const cityMessage = document.getElementById("city_message");
    const pincodeMessage = document.getElementById("pincode_message");

    function updateSummary() {

        if (paymentMethod.value === "ONLINE") {

            codLabel.innerHTML = "Online Payment Discount";

            codChargeValue.innerHTML =
                "- ₹ " + codCharge.toFixed(2);

            payToday.innerHTML =
                "₹ " + totalWithoutCOD.toFixed(2);

            payLater.innerHTML =
                "₹ 0";
            
            paymentNote.innerHTML =
            "✔ Fully paid online. Nothing to pay at delivery.";

            totalPayable.innerHTML =
                "₹ " + totalWithoutCOD.toFixed(2);

            totalSavings.innerHTML =
                (productSavings + codCharge).toFixed(2);

            savingsBreakdown.innerHTML =
                "₹ " + productSavings.toFixed(2) +
                " Product Discount<br>" +
                "₹ " + codCharge.toFixed(2) +
                " Online Payment Benefit";

        } else {

                codLabel.innerHTML = "COD Processing";

                payToday.innerHTML =
                    "₹ " + codPayNow.toFixed(2);

                payLater.innerHTML =
                    "₹ " + codPayLater.toFixed(2);

                paymentNote.innerHTML =
                    "Balance payable on delivery.";

        }

    }



    function showSuccess(input, messageElement, message) {
        input.classList.remove("border-red-500");
        input.classList.add("border-green-500");

        messageElement.textContent = "✓ " + message;
        messageElement.className = "text-xs mt-2 text-green-600";
    }

    function showError(input, messageElement, message) {
        input.classList.remove("border-green-500");
        input.classList.add("border-red-500");

        messageElement.textContent = "✗ " + message;
        messageElement.className = "text-xs mt-2 text-red-600";
    }

    function clearValidation(input, messageElement) {
        input.classList.remove("border-green-500", "border-red-500");

        messageElement.textContent = "";
        messageElement.className = "text-xs mt-2 hidden";
    }

    function validateCustomerName() {

        const value = customerName.value.trim();

        if (value === "") {
            clearValidation(customerName, customerNameMessage);
            return;
        }

        const regex = /^[A-Za-z ]{2,50}$/;

        if (regex.test(value)) {

            showSuccess(
                customerName,
                customerNameMessage,
                "Name looks good"
            );

        } else {

            showError(
                customerName,
                customerNameMessage,
                "Enter a valid full name"
            );

        }

    }

    customerName.addEventListener("input", validateCustomerName);

    paymentMethod.addEventListener("change", updateSummary);
    updateSummary();

});




