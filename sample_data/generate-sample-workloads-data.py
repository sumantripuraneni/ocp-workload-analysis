import pandas as pd
import random
import json

def generate_sample_workloads(num_records=100):
    kinds = ["Deployment", "StatefulSet", "DaemonSet", "Job", "CronJob"]
    namespaces = ["frontend", "backend", "database", "logging", "monitoring", "security", "payments"]
    
    data = []
    
    for i in range(num_records):
        kind = random.choice(kinds)
        ns = random.choice(namespaces)
        app_name = f"sample-app-{i}"
        
        # --- Resource Logic (Math-Ready Integers) ---
        # Using -1 for undefined to match your audit script fallback
        cpu_req = random.choice([250, 500, 1000, 2000, -1])
        cpu_lim = cpu_req * 2 if cpu_req != -1 else -1
        
        mem_req = random.choice([512, 1024, 2048, 4096, -1])
        mem_lim = mem_req * 2 if mem_req != -1 else -1
        
        # --- Storage Complexity ---
        pvc_cnt = random.randint(1, 3) if kind == "StatefulSet" else random.randint(0, 1)
        storage_comp = "None"
        if pvc_cnt > 0:
            storage_comp = random.choice(["RWO", "RWO", "RWX"]) # RWO is more common
            
        # --- Container Topology ---
        init_c = random.choice([0, 0, 0, 1])
        sidecars = random.choice([0, 0, 1, 2])
        total_c = 1 + init_c + sidecars
        
        # --- Networking & Exposure ---
        has_svc = random.choice([True, False])
        svc_names = f"{app_name}-svc" if has_svc else "None"
        exp_type = random.choice(["ClusterIP", "NodePort", "LoadBalancer", "Route", "Ingress"]) if has_svc else "Internal"
        is_ext = "Yes" if exp_type in ["LoadBalancer", "Route", "Ingress"] else "No"

        # --- Ordered Dictionary matching your exact field list ---
        row = {
            "Kind": kind,
            "Namespace": ns,
            "Name": app_name,
            "Replicas": 1 if kind in ["Job", "CronJob", "DaemonSet"] else random.randint(1, 5),
            "Schedule": "0 * * * *" if kind == "CronJob" else "N/A",
            "CPU_Request_Milli": cpu_req,
            "CPU_Limit_Milli": cpu_lim,
            "Mem_Request_MiB": mem_req,
            "Mem_Limit_MiB": mem_lim,
            "Init_Containers": init_c,
            "Sidecars": sidecars,
            "Total_Containers": total_c,
            "PVC_Count": pvc_cnt,
            "Storage_Complexity": storage_comp,
            "Services": svc_names,
            "Exposure_Type": exp_type,
            "Exposed_Externally": is_ext,
            "HPA_Enabled": "Yes" if (kind == "Deployment" and random.random() > 0.7) else "No",
            "VPA_Enabled": "Yes" if (kind == "Deployment" and random.random() > 0.9) else "No",
            "Node_Selector": random.choice(["Yes", "No", "No", "No"]),
            "Affinity_Rules": random.choice(["Yes", "No", "No"]),
            "Host_Network": random.choice(["No", "No", "No", "Yes"]),
            "Privileged": random.choice(["No", "No", "No", "Yes"]),
            "Liveness_Probe": random.choice(["Yes", "Yes", "No"]),
            "Readiness_Probe": random.choice(["Yes", "Yes", "No"]),
            "Additional_Networks": random.choice([0, 0, 0, 1, 2]),
            "ConfigMap_Count": random.randint(1, 8),
            "Secret_Count": random.randint(1, 5)
        }
        data.append(row)
    
    return data

if __name__ == "__main__":
    # Generate 100 sample records
    sample_data = generate_sample_workloads(100)
    
    # Create DataFrame
    df = pd.DataFrame(sample_data)
    
    # Define Filenames
    csv_file = 'k8s_workload_inventory.csv'
    json_file = 'k8s_workload_inventory.json'
    
    # Save to CSV
    df.to_csv(csv_file, index=False)
    
    # Save to JSON
    with open(json_file, 'w') as f:
        json.dump(sample_data, f, indent=4)
        
    print(f"✅ Generated {len(df)} sample workloads with 28 complexity fields.")
    print(f"📂 CSV Saved: {csv_file}")
    print(f"📂 JSON Saved: {json_file}")

    # Output column list to verify order
    print("\nColumn Order Verification:")
    print(", ".join(df.columns.tolist()))
