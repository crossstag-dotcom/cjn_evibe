async function validatePincode() {

    const value = pincode.value.trim();

    if (value.length === 0) {
        clearValidation(pincode, pincodeMessage);
        city.value = "";
        return;
    }

    if (!/^\d{6}$/.test(value)) {

        showError(
            pincode,
            pincodeMessage,
            "PIN must contain 6 digits"
        );

        city.value = "";

        return;
    }

    pincodeMessage.textContent = "Checking PIN...";
    pincodeMessage.className = "text-xs mt-2 text-blue-600";

    try {

        const response = await fetch(
            `/ajax/pincode/?pincode=${value}`
        );

        const data = await response.json();

        if (data.success) {

            city.value = data.city;

            showSuccess(
                pincode,
                pincodeMessage,
                "Service available"
            );

            showSuccess(
                city,
                cityMessage,
                data.city
            );

        } else {

            city.value = "";

            showError(
                pincode,
                pincodeMessage,
                data.message
            );

            clearValidation(city, cityMessage);

        }

    } catch (error) {

        city.value = "";

        showError(
            pincode,
            pincodeMessage,
            "Network error"
        );

        clearValidation(city, cityMessage);

    }

}