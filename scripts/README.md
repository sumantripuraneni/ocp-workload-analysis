# ☸️ Kubernetes Inventory Collector

This toolset automates the extraction of Namespace and Workload metadata from a Kubernetes cluster (Minikube/OCP) to prepare data for migration analysis.

---

## 📂 Component Overview

| File | Responsibility |
| :--- | :--- |
| **`run.sh`** | The orchestrator. Sets up the `venv`, installs dependencies, and runs the auditors. |
| **`scripts/namespace-inventory.py`** | **Namespace Data Collector: ** Capture namespace dtails
| **`scripts/workloads-inventory.py`** | **Workload Data Collector:** Captures CPU/Mem limits, Init Containers, and Sidecars per Deployment/STS/Job. |

---

## 🚀 Quick Start

1. **Ensure your cluster is active:**
   ```bash
   minikube status  # or oc whoami
