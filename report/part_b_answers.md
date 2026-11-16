# Part B: FreshCart ELT Technical Reference & Solutions

## B1. Baseline Execution Summary
- **Database Architecture:** Snowflake Medallion (Raw Landing $\rightarrow$ Bronze $\rightarrow$ Silver Cleanse \& Dedup $\rightarrow$ Dimensions SCD2 $\rightarrow$ Gold Fact Table)
- **Baseline Verification Metrics:**
  - Raw order rows in bronze after one run: **8** (6 web + 2 mobile)
  - Rows that pass cleaning (`silver.orders_clean`): **6**
  - Rows in quarantine: **2** (`ORD-1004`, `ORD-1006`)
  - Orders after deduplication (`silver.orders_dedup`): **4**
  - Final gold line: **4 orders, revenue ₹7,785.00, 126 loyalty points**
  - Share of rows rejected: **25%** (2 out of 8 total rows)

---

## B2. Detailed Hand Trace (ORD-1003 & ORD-1005)
*(Refer to `report/part_b_hand_trace.md` for full query expressions, schema drift comparisons, and arithmetic.)*

- **ORD-1003 Mobile vs Web:** Mobile record carries `updated_at = 2026-09-02 18:40:00`, which supersedes the web record (`09:10:00`). Dedup via `QUALIFY ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY updated_at DESC, ingest_seq DESC) = 1` retains the mobile row with `amount = 2100.00`.
- **ORD-1003 Points:** Platinum tier (multiplier 3). $\text{FLOOR}(2100 / 100) \times 3 = 63\text{ points}$.
- **ORD-1001 vs ORD-1005:** Priya's tier changes from Silver to Gold on `2026-09-03`. The point-in-time join `BETWEEN c.valid_from AND c.valid_to` assigns Silver (multiplier 1 $\rightarrow$ 12 pts) for ORD-1001 on `2026-09-01`, and Gold (multiplier 2 $\rightarrow$ 16 pts) for ORD-1005 on `2026-09-03`.

---

## B3. Currency Validation Rule & Quarantine Analysis

### Implementation in `SQL_10_ORDERS_CLEAN`:
```sql
ARRAY_CONSTRUCT_COMPACT(
  IFF(order_id IS NULL, 'missing_order_id', NULL),
  IFF(email IS NULL OR NOT REGEXP_LIKE(email, '^[^@\\s]+@[^@\\s]+\\.[a-z]{2,}$'), 'bad_email', NULL),
  IFF(pincode IS NULL OR NOT REGEXP_LIKE(pincode, '^[1-9][0-9]{5}$'), 'bad_pincode', NULL),
  IFF(order_date IS NULL, 'unparseable_date', NULL),
  IFF(updated_at IS NULL, 'unparseable_updated_at', NULL),
  IFF(amount <= 0, 'non_positive_amount', NULL),
  IFF(currency NOT IN ('INR', 'USD'), 'unsupported_currency', NULL)
) AS reasons
```

### Analysis:
1. **Reasons array for ORD-1006:**
   - **Before change:** `["bad_email", "bad_pincode"]`
   - **After change:** `["bad_email", "bad_pincode", "unsupported_currency"]`
2. **Does the Gold total change?**
   - **No.** ORD-1006 was already quarantined during the first run due to `bad_email` and `bad_pincode`. Since it was never part of `silver.orders_clean` (`WHERE ARRAY_SIZE(reasons) = 0`), adding a third rejection reason does not alter the set of clean orders advancing to Gold.
3. **Does the new run add a second quarantine row for ORD-1006?**
   - **No.** The `INSERT INTO quarantine.orders` query explicitly prevents duplicate quarantine entries via an anti-join:
     ```sql
     AND NOT EXISTS (
           SELECT 1 FROM quarantine.orders q
           WHERE q.source = c.source
             AND EQUAL_NULL(q.order_id, c.order_id)
             AND EQUAL_NULL(q.row_data:UPDATED_AT::TIMESTAMP_NTZ, c.updated_at))
     ```
     Because a record with source `'web'`, `order_id = 'ORD-1006'`, and `updated_at = '2026-09-04 08:30:00'` already exists in `quarantine.orders`, the `NOT EXISTS` condition evaluates to `FALSE`, preventing re-insertion.

---

## B4. SCD2 Change History & Idempotency Predictions

### Pre-Execution Predictions vs Actuals:
| Quantity | Your Prediction | Actual After Run |
| :--- | :--- | :--- |
| **Rows for CUST-02 in `dim.customers_scd2`** | **2** | 2 |
| **Tier used for ORD-1002** | **Gold** | Gold |
| **Loyalty points for ORD-1002** | **70** | 70 |
| **Total loyalty points in gold** | **161** | 161 |
| **Number of gold rows whose `published_at` changed** | **1** | 1 |

### Explanation of Idempotency & Bronze Growth:
1. **How `row_hash` and `MERGE` ensure idempotency:**  
   The `MERGE INTO gold.fct_orders` statement hashes all non-key transaction attributes into `row_hash`. The clause `WHEN MATCHED AND t.row_hash <> s.row_hash THEN UPDATE` only modifies records where an underlying attribute has actually changed. If pipeline data is identical upon re-execution, Snowflake executes 0 updates and 0 inserts on existing keys, leaving timestamps (`published_at`) and rows intact.
2. **Why Bronze grows by 8 rows on every run:**  
   Bronze is designed as an immutable, append-only raw landing layer. It preserves an exact historical log of raw files arriving from API batches without deduplication or mutation, ensuring full auditability and the ability to replay historical data pipelines from scratch if transformation logic changes.

---

## B5. Custom Data Quality Check & ELT vs ETL

### Selected Quality Check:
`"orders in silver.orders_dedup with future order date"`:
```sql
SELECT COUNT_IF(order_date > CURRENT_DATE()) FROM silver.orders_dedup
```
- **Normal state:** Returns `0` (`OK`).
- **Failure test:** Adding mock order with `order_date = '2030-01-01'` triggers `1` (`PROBLEM`).
- **Post-removal:** Returns `0` (`OK`).

### Why ELT is Superior for FreshCart vs When ETL Still Wins:
- **Why ELT is better for FreshCart:** FreshCart ingests heterogeneous raw JSON payloads from multiple decoupled endpoints (mobile apps and web stores) whose schemas frequently drift. Loading raw JSON directly into Snowflake Bronze preserves 100% of the raw data without data loss, enabling transformations, schema corrections, and deduplication to occur at massive parallel scale inside the cloud data warehouse using SQL.
- **When ETL would still win:** ETL remains superior in scenarios involving **sensitive PII/compliance constraints** (e.g., masking patient healthcare records or credit card numbers in-flight before entering cloud storage) or when bandwidth and cloud warehouse storage costs prohibit loading high-volume, low-value raw streaming logs that must be pre-aggregated and filtered before ingestion.
