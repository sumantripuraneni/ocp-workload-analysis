import pandas as pd
import random
import json

namespaces_list = []
env_types = ["prod", "dev", "staging", "infra", "qa", "batch"]
app_names = ["checkout", "payment", "auth", "search", "inventory", "logging", "metrics", "etl", "db", "frontend"]

for i in range(1, 101):
    env = random.choice(env_types)
    app = random.choice(app_names)
    name = f"{env}-{app}-{i:02d}"
    
    # Logic to make data realistic based on environment
    if env == "prod":
        deps = random.randint(3, 15)
        pods = deps * random.randint(2, 5) # High replicas
        net_pol = random.randint(2, 8)    # High security
        pvcs = random.randint(0, 2)
    elif env == "batch":
        deps = 0
        pods = random.randint(10, 100)    # Many short-lived pods
        net_pol = random.randint(0, 2)
        pvcs = 0
    elif env == "infra":
        deps = random.randint(1, 4)
        pods = random.randint(5, 20)
        net_pol = 0                        # Often overlooked
        pvcs = random.randint(1, 5)
    else: # dev/staging
        deps = random.randint(1, 3)
        pods = deps * 1                   # Low replicas
        net_pol = random.choice([0, 1])
        pvcs = 0

    row = {
        "Namespace": name,
        "Status": "Active",
        "Deployments": deps,
        "StatefulSets": random.randint(0, 2) if env in ["prod", "db", "infra"] else 0,
        "DaemonSets": 1 if env == "infra" else 0,
        "Pods": pods,
        "Jobs": random.randint(20, 100) if env == "batch" else random.randint(0, 5),
        "CronJobs": random.randint(1, 10) if env == "batch" else random.randint(0, 2),
        "PVCs": pvcs,
        "NetworkPolicies": net_pol,
        "Ingress": random.randint(1, 3) if env == "prod" else 0,
        "Services": deps + 1,
        "ConfigMaps": random.randint(5, 30),
        "Secrets": random.randint(5, 20)
    }
    namespaces_list.append(row)

# Save to CSV
df = pd.DataFrame(namespaces_list)
df.to_csv("k8s_ns_100_sample.csv", index=False)

# Save to JSON
with open("k8s_ns_100_sample.json", "w") as f:
    json.dump(namespaces_list, f, indent=4)

print("Generated 100-row sample: k8s_ns_100_sample.csv and .json")
