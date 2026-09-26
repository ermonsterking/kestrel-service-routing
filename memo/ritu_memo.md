# Kestrel Home — Service Routing Model
## Decision Memo for Ritu

### Decision

The replacement routing model is ready for controlled operational rollout.

It achieved **96.49% accuracy** on a chronological validation set, exceeding the requested 90% historical-routing match target by **6.49 percentage points**. The final model was trained using customer request text plus request-time metadata: channel, product family, warranty status, and source.

The model predicts the current seven service queues and does not use post-routing information such as final team, transfers, or resolution time.

### What we built

We evaluated three increasingly capable local models:

- Word TF-IDF + LinearSVC: **94.09%**
- Word + character TF-IDF + LinearSVC: **95.66%**
- Word + character TF-IDF + request metadata + LinearSVC: **96.49%**

The final model was retrained on all **10,822 labelled historical requests** and generated predictions for all **2,178 test requests**.

### What the evidence says

The validation set contained 2,165 requests. The final model classified **2,089 correctly** and **76 incorrectly**, giving a **3.51% error rate**.

The remaining errors are concentrated around ambiguous or multi-intent requests. The largest confusion was Repairs being predicted as Filters & Consumables in 11 cases. Other recurring patterns involved combinations of faults with payment, warranty, installation, returns, or consumables.

Water Purifier requests had the highest validation error rate at **5.86%**, indicating that this product category deserves particular monitoring during rollout.

### Business context

The current routing bot costs **₹3.2 lakh per year**.

Historical operational data contains **3,902 transfers** across the 10,822 labelled requests, with **2,696 requests involving at least one transfer**. After normalizing the two renamed teams, 2,471 requests had a different first and final team.

Using the policy's stated ₹305 transfer cost and ₹260 additional-contact assumption gives an illustrative historical operational cost of approximately **₹18.3 lakh** over the 18-month training period. This is an estimate based on the provided policy assumptions, not an audited savings figure.

The replacement's actual monthly infrastructure cost should be measured during deployment rather than assumed from the validation result.

### Next steps

1. Deploy the model behind the routing API in a controlled rollout.
2. Monitor routing accuracy, transfer rate, and customer re-contact rate.
3. Review low-confidence or ambiguous cases, especially fault + consumable, fault + warranty, and payment + service requests.
4. Monitor Water Purifier requests separately because they showed the highest validation error rate.
5. Compare operational metrics against the existing routing process before fully retiring the legacy bot.

### Monday handoff

The incoming team should receive:

- The trained model and reproducible training code.
- Validation metrics, confusion pairs, and representative failure cases.
- The API and Streamlit demonstration.
- The prediction file for the supplied test set.

The model should be retrained or reviewed if product categories, team definitions, routing policy, or request patterns change materially.