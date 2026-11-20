# EVIBE Business Rules v1

Last Updated: June 2026

---

# 1. Core Principle

Business decisions must be controlled through configuration whenever possible.

Client requests:

- Change reward percentage
- Change shipping charge
- Change COD charge
- Enable/disable COD
- Enable/disable rewards
- Launch festival offer
- Change minimum order requirement

These changes must be possible without source code modifications.

---

# 2. Shipping Rules

Configuration:

- Shipping Per Pant

Formula:

Shipping Charge =
Shipping Per Pant × Quantity

Example:

1 Pant = ₹149
2 Pants = ₹298
3 Pants = ₹447

No free shipping in Phase 1.

---

# 3. COD Rules

Configuration:

- COD Enabled
- COD Charge
- Max COD Order Value

Formula:

COD Charge =
COD Charge Per Pant × Quantity

Example:

1 Pant = ₹50
2 Pants = ₹100
3 Pants = ₹150

---

# 4. Billing Model

## Prepaid

Customer Pays:

Product Price +
Shipping Charge

Example:

₹799 + ₹149 = ₹948

---

## COD

Order Value:

Product Price +
Shipping Charge +
COD Charge

Example:

₹799 + ₹149 + ₹50 = ₹998

Customer Pays Now:

Shipping Charge +
COD Charge

Example:

₹149 + ₹50 = ₹199

Customer Pays At Delivery:

Product Price

Example:

₹799

---

# 5. Order Financial Fields

Order stores:

- subtotal
- shipping_charge
- cod_charge
- total_amount
- advance_paid_amount
- amount_collectable

---

# 6. Reward System

Configuration:

- Reward Enabled
- Reward Percentage
- Minimum Pants For Reward
- Reward Requires Exchange Waiver

---

# 7. Reward Eligibility

Reward can be used only when:

Cart Quantity >= Minimum Pants For Reward

Example:

Minimum Pants = 4

1 Pant = Not Eligible
2 Pants = Not Eligible
3 Pants = Not Eligible
4 Pants = Eligible

---

# 8. Reward Calculation

Reward Base:

Product Total +
Shipping Total

Exclude:

COD Charge

Example:

Product = ₹799
Shipping = ₹149
COD = ₹50

Reward Base = ₹948

---

# 9. Reward Customer Choice

If eligible:

Customer must choose:

- Apply Reward
- Continue Without Reward

Reward must never be forced.

---

# 10. Reward Consequences

If reward is applied:

Discount Applied

Exchange Allowed:

Determined by configuration.

Example:

Reward Requires Exchange Waiver = True

Then:

Exchange Allowed = False

---

# 11. Festival Offers

Festival offers are independent from Store Configuration.

Festival Offer Fields:

- Title
- Banner Text
- Discount Percentage
- Minimum Pants Required
- Exchange Allowed
- Start Date
- End Date
- Active

Examples:

- Ganesh Festival Offer
- Eid Offer
- Diwali Sale

---

# 12. Offer Selection Rule

Only one offer may be applied per order.

Offer stacking is prohibited.

Customer chooses one:

- Reward Offer
- Festival Offer
- No Offer

Example:

Reward = 5%

Festival = 10%

Customer selects one.

Customer cannot combine both.

---

# 13. Manual Logistics (Phase 1)

No Shiprocket integration.

No NimbusPost integration.

No ClickPost integration.

No Shipway integration.

No iThink Logistics integration.

Admin manually enters:

- Courier Name
- AWB
- Tracking Link
- Shipment Status

---

# 14. Order Lifecycle

CREATED

PAID

PROCESSING

PACKED

READY_TO_SHIP

SHIPPED

OUT_FOR_DELIVERY

DELIVERED

RTO

CANCELLED

---

# 15. Analytics

Track:

- Orders
- Revenue
- COD Revenue
- Prepaid Revenue
- Shipping Revenue
- RTO
- Returns
- Reward Usage
- Festival Offer Usage
- Top Products

---

# 16. Architecture Rule

If client requests a business rule change:

Preferred Solution:
Configuration Change

Avoid:
Source Code Change