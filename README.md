# ocp-workload-analysis

# OpenShift Workload & Namespace Complexity Analysis

This project provides an automated framework for analyzing Kubernetes/OpenShift inventories to estimate migration effort. It uses a weighted complexity model to categorize Workloads and Namespaces into **Small**, **Medium**, and **Large** tiers, generating a predictive **Migration Velocity** timeline.

## 🚀 Key Features

* **Weighted Grading Engine:** Scans inventory for CPU/Memory requests, PVC presence, and networking complexity.
* **Namespace Governance Analysis:** Calculates "Plumbing" effort (RBAC, Quotas, NetworkPolicies).
* **Predictive Velocity Dashboard:** Generates a linear burn-up chart showing estimated completion dates based on engineering man-hours.
* **Configurable Levers:** All complexity weights and labor hours are driven by JSON files, allowing for instant "What-if" scenario planning.

---

## 🛠 Project Structure

* `configs/`: Contains `migration_config.json` (effort hours) and complexity weightings.
* `scripts/`: Core Python logic for workload and namespace grading.
* `sample_data/`: Input directory for raw CSV inventory exports.
* `outputs/`: Generated analysis and velocity charts.
* `migration-analysis.ipynb`: The primary executive dashboard.

---

## 💻 Setup & Installation

```bash
# 1. Clone and Initialize
git clone https://github.com/sumantripuraneni/ocp-workload-analysis.git
cd ocp-workload-analysis

# 2. Create Virtual Environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Run Analysis
jupyter notebook migration-analysis.ipynb

