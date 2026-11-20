document.addEventListener("DOMContentLoaded", function () {

    const orderField = document.getElementById("id_order");
    const orderItemField = document.getElementById("id_order_item");

    if (!orderField || !orderItemField) return;

    orderField.addEventListener("change", function () {

        const orderId = this.value;

        orderItemField.innerHTML = "<option>Loading...</option>";

        fetch(`/ajax/order-items/?order_id=${orderId}`)
            .then(res => res.json())
            .then(data => {

                orderItemField.innerHTML = "<option value=''>Select item</option>";

                data.items.forEach(item => {
                    const option = document.createElement("option");
                    option.value = item.id;
                    option.text = item.text;
                    orderItemField.appendChild(option);
                });
            });

    });

});