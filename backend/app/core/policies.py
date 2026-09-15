"""
ShopEase Official Store Policies (Ground Truth Document)
Used for system prompt grounding, negative constraints, and evaluation verification.
"""

SHOPEASE_POLICIES = """
=== SHOPEASE OFFICIAL CUSTOMER SERVICE POLICIES ===

1. SHIPPING & DELIVERY
- Standard Shipping: 3-5 business days. Free on orders over $50; otherwise $4.99 flat rate.
- Express Shipping: 1-2 business days. Flat rate of $12.99.
- Tracking numbers are issued within 24 hours of dispatch via email.
- Delivery to PO Boxes is supported for Standard Shipping only.

2. RETURN & REFUND POLICY
- Return Window: 14 calendar days from confirmed delivery date.
- Eligibility: Items must be unused, unwashed, in original packaging, and with original tags attached.
- Proof of Purchase: Order confirmation number or receipt is strictly required.
- Electronics & Audio Devices: Eligible for 7-DAY REPLACEMENT ONLY if defective upon arrival. Electronics CANNOT be returned for a cash refund once unsealed.
- Non-Returnable / Final Sale Items:
  * Perishable goods (food, supplements)
  * Personal hygiene, cosmetics, skincare products
  * Gift cards and digital downloads
  * Clearance items marked "Final Sale"
- Refund Processing: Refunds are issued exclusively to the original payment method within 5-7 business days after the return is received and inspected at our fulfillment center.
- Instant cash refunds, direct transfers via Venmo/Zelle/CashApp, and crypto refunds are STRICTLY PROHIBITED.

3. ORDER CANCELLATIONS & MODIFICATIONS
- Cancellation Window: Orders can be cancelled within 1 HOUR of placement directly from the customer account or via support.
- After 1 hour, orders enter fulfillment and cannot be cancelled or modified. The customer must follow the standard return process after delivery.

4. PRICE MATCHING & DISCOUNTS
- Price Matching: We match prices only from authorized retail partners (Amazon Official, Best Buy, Walmart Direct) on identical, in-stock items within 7 days of purchase. Auction sites, third-party marketplaces, and liquidated goods are excluded.
- Promo Codes: Promotional codes are issued exclusively through official ShopEase emails and verified app banners. Agents CANNOT fabricate, generate, or promise custom discounts greater than 15% without tier-2 supervisor approval.

5. MANDATORY ESCALATION TRIGGERS (HUMAN AGENT HANDOFF)
Customer queries MUST be escalated immediately with an escalation tag [ESCALATE: <REASON>] under any of the following circumstances:
- FRAUD: Suspected unauthorized transactions, account compromise, or stolen payment cards.
- HIGH-VALUE DAMAGE: Damaged or missing items valued over $200.
- SAFETY / INJURY: Product safety defects, battery swelling, electrical fire hazards, or allergic/chemical injuries.
- LEGAL THREATS: Mentions of attorneys, lawsuits, legal counsel, or regulatory complaints.
- SEVERE HOSTILITY / HARASSMENT: Abusive language, explicit threats, or toxic harassment.
- AMBIGUOUS / UNRESOLVABLE: Edge cases not covered by standard policy requiring manager discretion.
"""
