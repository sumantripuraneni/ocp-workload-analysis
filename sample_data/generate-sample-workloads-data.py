import pandas as pd
import random
import json

# Lists for random generation
kinds = ["Deployment", "StatefulSet", "DaemonSet", "Job", "CronJob"]
namespaces = ["prod", "staging", "qa", "infra", "database", "security"]
apps = ["auth", "payment", "logger", "worker", "cache", "api", "proxy", "db", "search", "billing"]
schedules = ["0 * * * *", "*/15 * * * *", "0 2 * * *", "0 0 * * 0"]

data = []

for i in range(1, 101):
    kind = random.choice(kinds)
    ns = random.choice(namespaces)
    app_name = f"{random.choice(apps)}-{i}"
    
    # Logic for complexity variation
    if kind == "StatefulSet":
        cpu = f"{random.randint(2, 8)}"
        mem = f"{random.randint(4, 16)}Gi"
        pvc = 1
    elif kind == "CronJob":
        cpu = f"{random.randint(500, 2000)}m"
        mem = f"{random.randint(1, 4)}Gi"
        pvc = 0
    else:
        cpu = f"{random.randint(100, 1000)}m"
        mem = f"{random.randint(128, 1024)}Mi"
        pvc = 0

    has_init = random.choice(["Yes", "No"])
    has_side = random.choice(["Yes", "No"])
    
    row = {
        "Kind": kind,
        "Namespace": ns,
        "Name": app_name,
        "Schedule": random.choice(schedules) if kind == "CronJob" else "N/A",
        "CPU_Limit": cpu,
        "Mem_Limit": mem,
        "Has_Init": has_init,
        "Init_Names": "setup-container" if has_init == "Yes" else "",
        "Has_Sidecars": has_side,
        "Sidecar_Names": "istio-proxy" if has_side == "Yes" else "",
        "PVC_Count": pvc,
        "ConfigMap_Count": random.randint(0, 5),
        "Secret_Count": random.randint(1, 4),
        "Total_Containers": (1 if has_init == "No" else 2) + (1 if has_side == "Yes" else 0)
    }
    data.append(row)

# Export to CSV
df = pd.DataFrame(data)
df.to_csv("k8s_sample_100_rows.csv", index=False)

# Export to JSON
with open("k8s_sample_100_rows.json", "w") as f:
    json.dump(data, f, indent=4)

print("Generated k8s_sample_100_rows.csv and k8s_sample_100_rows.json successfully.")