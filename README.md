# FreshCart Data Platform: From Git to Gold
**Version Control, ELT, ML Pipelines, and Event Streaming — End to End**

**Student Name:** Kothakota Chandra Raju  
**Roll Number:** 23BCS138  
**Course:** Data Engineering  
**Repository:** [https://github.com/ChandraRaju369/freshcart-pipelines](https://github.com/ChandraRaju369/freshcart-pipelines)

---

## 1. Project Overview
This repository contains the end-to-end implementation of an enterprise-grade data platform demonstrating the four pillars of modern data engineering:
1. **Version Control & CI/CD (Part A):** Git repository workflow with automated GitHub Actions testing and quality gating on Python 3.12.
2. **FreshCart ELT on Snowflake (Part B):** Medallion architecture (Raw $\rightarrow$ Bronze $\rightarrow$ Silver $\rightarrow$ Quarantine $\rightarrow$ SCD Type 2 Dims $\rightarrow$ Gold) with currency validation, deduplication via `QUALIFY ROW_NUMBER()`, and idempotency.
3. **Mage ML Pipeline (Part C):** Orchestrated Iris classification DAG (`load_iris` $\rightarrow$ `prepare_data` $\rightarrow$ `train_model` $\rightarrow$ `save_results` & `evaluate_model`) enforcing runtime test-gate controls.
4. **RabbitMQ Event Streaming (Part D):** Topic-exchange (`rapido-dispatch`) real-time ride/food dispatching system with dynamic binding patterns, message consumer ACKs, and malformed-message NACK handling.
5. **Architectural Integration & Technical Report (Part E):** Unified data platform architecture connecting streaming events to lakehouse analytics.

---

## 2. Directory Layout
```text
freshcart-pipelines/
├── .github/
│   └── workflows/
│       └── ci.yml                # Automated CI pipeline running pytest on push
├── elt/
│   └── freshcart_elt.ipynb       # FreshCart Medallion ELT notebook on Snowflake
├── iris_project/                 # Mage ML classification project
│   ├── data_loaders/
│   ├── transformers/
│   ├── data_exporters/
│   └── pipelines/
├── stream/
│   ├── dispatcher.py             # RabbitMQ topic event publisher
│   └── driver.py                 # RabbitMQ driver consumer with ACK/NACK logic
├── tests/
│   └── test_prepare_data.py      # Pytest validation for 80/20 train-test split
├── evidence/                     # Audit trail screenshots across all parts
│   ├── part_a/
│   ├── part_b/
│   ├── part_c/
│   ├── part_d/
│   └── part_e/
├── report/                       # Final PDF report and diagrams
├── .gitignore                    # Secrets & artifact ignore rules
├── requirements.txt              # Project dependencies
└── README.md                     # Project documentation
```

---

## 3. Getting Started

### Prerequisites
- Python 3.12+
- Git
- Snowflake Account (with compute warehouse and SYSADMIN / ACCOUNTADMIN roles)
- RabbitMQ broker (local or CloudAMQP)

### Local Environment Setup
```powershell
# Clone the repository
git clone https://github.com/ChandraRaju369/freshcart-pipelines.git
cd freshcart-pipelines

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install project dependencies
pip install -r requirements.txt
```

### Running Tests
```powershell
pytest -v tests/
```
