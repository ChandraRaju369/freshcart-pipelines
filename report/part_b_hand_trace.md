# Part B2: Hand Tracing Analysis for ORD-1003 and ORD-1005

## 1. Deep Dive Trace: ORD-1003

### Step 1: Raw Records in `bronze.orders_raw` and Schema Drift
ORD-1003 arrives from two heterogeneous data sources:

#### Record A — Web E-commerce Store (`source = 'web'`):
```json
{
  "order_id": "ORD-1003",
  "cust_email": "meera@outlook.com",
  "cust_name": "MEERA S",
  "order_date": "2026-09-02",
  "amount": null,
  "currency": "INR",
  "pincode": "400050",
  "updated_at": "2026-09-02 09:10:00"
}
```

#### Record B — Mobile App Backend (`source = 'mobile'`):
```json
{
  "orderId": "ORD-1003",
  "customer": {
    "email": "Meera@Outlook.com",
    "name": "Meera S"
  },
  "orderDate": "02/09/2026",
  "total": {
    "value": "2,100.00",
    "currency": "INR"
  },
  "deliveryPin": "400050",
  "updatedAt": "2026-09-02T18:40:00"
}
```

#### Why Field Names and Structures Differ:
1. **Naming Conventions:** The web platform uses flat JSON with snake_case attributes (`order_id`, `cust_email`, `cust_name`, `updated_at`), whereas the mobile application framework emits nested JSON structures with camelCase identifiers (`orderId`, `customer.email`, `deliveryPin`, `updatedAt`).
2. **Date Format Variations:** The web API emits ISO format (`YYYY-MM-DD`), whereas the mobile backend sends day-first dates (`DD/MM/YYYY`).
3. **Data Completeness:** The web order arrived incomplete (`amount: null`), representing a preliminary checkout draft, while the mobile session completed payment (`"total": {"value": "2,100.00"}`) with a later timestamp.

---

### Step 2: Normalization in `SQL_10_ORDERS_CLEAN` (`silver.orders_checked`)
`SQL_10_ORDERS_CLEAN` reconciles both JSON shapes into standardized relational columns using two CTEs (`unified` and `typed`):

1. **Mapping Unified Column Names:**
   - Web: `raw:order_id::STRING`, `raw:cust_email::STRING`, `raw:amount::STRING`
   - Mobile: `raw:orderId::STRING`, `raw:customer.email::STRING`, `raw:total.value::STRING`
2. **Transformation and Cleansing Expressions:**
   - **Email:** `LOWER(TRIM(cust_email))` $\rightarrow$ Converts `"Meera@Outlook.com"` to standard `"meera@outlook.com"`.
   - **Customer Name:** `INITCAP(RTRIM(TRIM(cust_name), '.'))` $\rightarrow$ `"Meera S"`.
   - **Order Date Normalization:**
     ```sql
     COALESCE(
       TRY_TO_DATE(order_date, 'YYYY-MM-DD'),
       TRY_TO_DATE(order_date, 'DD/MM/YYYY'),
       TRY_TO_DATE(order_date, 'MON DD, YYYY')
     )
     ```
     Correctly parses `"2026-09-02"` (web) and `"02/09/2026"` (mobile) into `2026-09-02`.
   - **Amount Extraction:**
     `TRY_TO_DECIMAL(REGEXP_REPLACE(amount, '[^0-9.-]', ''), 12, 2)`
     Strips commas (`"2,100.00"` $\rightarrow$ `2100.00`) and preserves `NULL` for the web record without throwing parse exceptions.
   - **Quality Rule Array:**
     `ARRAY_CONSTRUCT_COMPACT(...)` evaluates validity. Because `amount IS NULL` is intentionally permitted at this stage (flagged as `amount_missing = TRUE`), both records pass cleaning into `silver.orders_clean` with `ARRAY_SIZE(reasons) = 0`.

---

### Step 3: Deduplication in `SQL_20_ORDERS_DEDUP`
Both versions enter `silver.orders_clean`. Deduplication is enforced via Snowflake window functions:

```sql
SELECT *
FROM silver.orders_clean
QUALIFY ROW_NUMBER() OVER (
          PARTITION BY order_id
          ORDER BY updated_at DESC, ingest_seq DESC
        ) = 1;
```

#### Why the Mobile Copy Survives:
- The window function partitions by `order_id = 'ORD-1003'`.
- It orders candidates by `updated_at DESC`.
  - Mobile record: `updated_at = 2026-09-02 18:40:00`
  - Web record: `updated_at = 2026-09-02 09:10:00`
- Since `2026-09-02 18:40:00 > 2026-09-02 09:10:00`, the mobile record receives `ROW_NUMBER() = 1`.
- The incomplete web record receives `ROW_NUMBER() = 2` and is discarded. The surviving row carries `amount = 2100.00`.

---

### Step 4: Gold Enrichment & Loyalty Points Arithmetic
In `SQL_40_GOLD`, the surviving record is enriched via point-in-time dimension lookups:

1. **FX Conversion:**
   - Order currency is `INR`.
   - Joined to `ref.fx_daily` on currency and order date (`fx.rate_to_inr = 1.0`).
   $$\text{amount\_inr} = \text{ROUND}(2100.00 \times 1.0, 2) = 2100.00$$

2. **Customer Tier & Multiplier Lookup:**
   - Customer email `meera@outlook.com` joins `dim.customers_scd2` (`CUST-03`).
   - Order date `2026-09-02` falls within `valid_from = '2022-11-01'` and `valid_to = '9999-12-31'`.
   - Tier is `Platinum`.
   - Joins `ref.tier_multiplier` on `tier = 'Platinum'`, yielding `multiplier = 3`.

3. **Loyalty Points Calculation:**
   $$\text{loyalty\_points} = \text{FLOOR}\left(\frac{\text{amount\_inr}}{100}\right) \times \text{multiplier}$$
   $$\text{loyalty\_points} = \text{FLOOR}\left(\frac{2100.00}{100}\right) \times 3 = 21 \times 3 = 63\text{ points}$$

4. **High Value Order Flag:**
   $$\text{is\_high\_value} = (2100.00 \ge 2000.00) = \mathbf{TRUE}$$

---

## 2. Point-in-Time SCD Type 2 Trace: ORD-1001 vs ORD-1005 (Priya R)

### Customer SCD Type 2 Dimension Table (`dim.customers_scd2`)
Priya (`CUST-01`, `priya.r@gmail.com`) has two historical records:
- **Version 1 (Silver Tier):** `valid_from = '2023-04-10'`, `valid_to = '2026-09-02'`, `is_current = FALSE`
- **Version 2 (Gold Tier):** `valid_from = '2026-09-03'`, `valid_to = '9999-12-31'`, `is_current = TRUE`

### The Point-in-Time Join Condition in `SQL_40_GOLD`:
```sql
LEFT JOIN dim.customers_scd2 c
       ON  c.email = o.email
       AND o.order_date BETWEEN c.valid_from AND c.valid_to
```

### Comparison:
| Attribute | ORD-1001 | ORD-1005 |
| :--- | :--- | :--- |
| **Order Date** | `2026-09-01` | `2026-09-03` |
| **Matching SCD2 Interval** | `2023-04-10` to `2026-09-02` | `2026-09-03` to `9999-12-31` |
| **Applicable Tier** | **Silver** | **Gold** |
| **Multiplier** | `1` | `2` |
| **Amount INR** | ₹1,250.00 | ₹899.00 |
| **Points Formula** | $\text{FLOOR}(1250/100) \times 1$ | $\text{FLOOR}(899/100) \times 2$ |
| **Points Earned** | **12 points** | **16 points** |

**Conclusion:**  
Priya earns Gold tier points (multiplier 2) for ORD-1005 because the transaction took place on `2026-09-03`, the exact day her upgrade took effect. Conversely, ORD-1001 occurred on `2026-09-01`, when her active tier was Silver (multiplier 1). The SCD Type 2 architecture accurately preserves historical truth without retroactively corrupting past orders.
