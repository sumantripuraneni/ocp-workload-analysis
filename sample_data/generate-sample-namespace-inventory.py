import pandas as pd
import random
import json
from datetime import datetime, timedelta

def generate_sample_namespaces(num_records=50):
    # Common OpenShift/K8s namespace patterns
    ns_prefixes = ["prod", "dev", "staging", "uat", "shared", "cicd", "infra"]
    apps = ["billing", "crm", "auth", "inventory", "portal", "reporting", "cache"]
    
    data = []
    
    for i in range(num_records):
        # Generate a realistic name or use a system-like name
        if i < 5:
            name = ["openshift-logging", "openshift-monitoring", "kube-system", "default", "openshift-ingress"][i]
            status = "Active"
        else:
            name = f"{random.choice(ns_prefixes)}-{random.choice(apps)}-{random.randint(1, 5)}"
            status = random.choice(["Active", "Active", "Active", "Terminating"])

        # Governance & Security Logic
        has_quota = random.choice(["Yes", "No", "Yes"])
        net_pol_count = random.choice([0, 1, 1, 2, 5]) # Some have none, some have many
        egress_ips = random.choice([0, 0, 0, 1, 2])     # Egress IPs are rare
        ing_routes = random.randint(0, 8)              # Exposure count

        # Workload Aggregation Logic
        is_infra = "openshift" in name or "kube" in name
        
        deploys = 0 if is_infra else random.randint(0, 15)
        sts = 0 if is_infra else random.choice([0, 0, 1, 2])
        ds = random.choice([0, 0, 1]) if is_infra else 0
        jobs = random.randint(0, 5)
        cronjobs = random.randint(0, 3)
        
        # Totals
        pods = (deploys * 3) + (sts * 2) + ds + random.randint(1, 5)
        pvcs = sts + random.randint(0, 2) if sts > 0 else random.randint(0, 1)
        svcs = random.randint(1, 5) if deploys > 0 or sts > 0 else 0
        
        # Config Logic
        cms = random.randint(2, 20)
        secrets = random.randint(5, 25)
        
        # Metadata
        days_ago = random.randint(10, 500)
        creation_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")

        row = {
            "Namespace": name,
            "Status": status,
            "Resource_Quota": has_quota,
            "Network_Policy_Count": net_pol_count,
            "Egress_IP_Count": egress_ips,
            "Ingress_Routes": ing_routes,
            "Deployments": deploys,
            "StatefulSets": sts,
            "DaemonSets": ds,
            "Jobs": jobs,
            "CronJobs": cronjobs,
            "Total_Pods": pods,
            "Total_PVCs": pvcs,
            "Total_Services": svcs,
            "Total_ConfigMaps": cms,
            "Total_Secrets": secrets,
            "Labels_Count": random.randint(2, 10),
            "Creation_Date": creation_date
        }
        data.append(row)
    
    return data

if __name__ == "__main__":
    # Generate 50 sample namespaces
    sample_data = generate_sample_namespaces(50)
    
    # Create DataFrame
    df = pd.DataFrame(sample_data)
    
    # Filenames
    csv_file = 'k8s_namespace_inventory.csv'
    json_file = 'k8s_namespace_inventory.json'
    
    # Save to CSV
    df.to_csv(csv_file, index=False)
    
    # Save to JSON
    with open(json_file, 'w') as f:
        json.dump(sample_data, f, indent=4)
        
    print(f"✅ Generated {len(df)} sample namespaces.")
    print(f"📂 CSV Saved: {csv_file}")
    print(f"📂 JSON Saved: {json_file}")

    # Column order verification
    print("\nField List Verification:")
    print(" | ".join(df.columns.tolist()))
