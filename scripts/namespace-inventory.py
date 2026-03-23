import csv
import json
import pandas as pd
from kubernetes import client, config

def fetch_namespace_inventory():
    """Aggregates all K8s resources at the Namespace level."""
    config.load_kube_config()
    
    # Initialize APIs
    core_v1 = client.CoreV1Api()
    apps_v1 = client.AppsV1Api()
    batch_v1 = client.BatchV1Api()
    networking_v1 = client.NetworkingV1Api()
    
    namespaces = core_v1.list_namespace().items
    inventory = []

    print(f"Starting audit across {len(namespaces)} namespaces...")

    for ns in namespaces:
        name = ns.metadata.name
        status = ns.status.phase

        # 1. Apps & Controllers
        deploys = apps_v1.list_namespaced_deployment(name).items
        stss = apps_v1.list_namespaced_stateful_set(name).items
        daemons = apps_v1.list_namespaced_daemon_set(name).items
        
        # 2. Workload Instances
        pods = core_v1.list_namespaced_pod(name).items
        jobs = batch_v1.list_namespaced_job(name).items
        cronjobs = batch_v1.list_namespaced_cron_job(name).items
        
        # 3. Networking
        netpols = networking_v1.list_namespaced_network_policy(name).items
        ingresses = networking_v1.list_namespaced_ingress(name).items
        services = core_v1.list_namespaced_service(name).items
        
        # 4. Storage & Config
        pvcs = core_v1.list_namespaced_persistent_volume_claim(name).items
        configmaps = core_v1.list_namespaced_config_map(name).items
        secrets = core_v1.list_namespaced_secret(name).items

        data = {
            "Namespace": name,
            "Status": status,
            "Deployments": len(deploys),
            "StatefulSets": len(stss),
            "DaemonSets": len(daemons),
            "Pods": len(pods),
            "Jobs": len(jobs),
            "CronJobs": len(cronjobs),
            "PVCs": len(pvcs),
            "NetworkPolicies": len(netpols),
            "Ingress": len(ingresses),
            "Services": len(services),
            "ConfigMaps": len(configmaps),
            "Secrets": len(secrets)
        }
        inventory.append(data)
        print(f" - Audited: {name}")

    return inventory

if __name__ == "__main__":
    try:
        final_results = fetch_namespace_inventory()
        
        # Create DataFrame
        df = pd.DataFrame(final_results)
        
        # Save CSV
        df.to_csv('k8s_ns_inventory.csv', index=False)
        
        # Save JSON
        with open('k8s_ns_inventory.json', 'w') as f:
            json.dump(final_results, f, indent=4)
            
        print("\n" + "="*30)
        print("INVENTORY AUDIT SUCCESSFUL")
        print("="*30)
        print(f"Total Namespaces: {len(df)}")
        print(f"Total Workloads Identified: {df['Deployments'].sum() + df['StatefulSets'].sum()}")
        print("Files created in current directory:")
        print(" - k8s_ns_inventory.csv")
        print(" - k8s_ns_inventory.json")
        
    except Exception as e:
        print(f"❌ Error during Audit: {e}")
