import pandas as pd
import json
from kubernetes import client, config

def get_namespace_inventory():
    config.load_kube_config()
    
    # API Clients
    core_v1 = client.CoreV1Api()
    apps_v1 = client.AppsV1Api()
    batch_v1 = client.BatchV1Api()
    net_v1 = client.NetworkingV1Api()
    
    namespaces = core_v1.list_namespace().items
    inventory = []

    for ns in namespaces:
        name = ns.metadata.name
        print(f"Auditing Namespace: {name}...")

        # Core Resources
        pods = core_v1.list_namespaced_pod(name).items
        pvcs = core_v1.list_namespaced_persistent_volume_claim(name).items
        services = core_v1.list_namespaced_service(name).items
        configmaps = core_v1.list_namespaced_config_map(name).items
        secrets = core_v1.list_namespaced_secret(name).items
        
        # Apps Resources
        deployments = apps_v1.list_namespaced_deployment(name).items
        statefulsets = apps_v1.list_namespaced_stateful_set(name).items
        daemonsets = apps_v1.list_namespaced_daemon_set(name).items
        
        # Batch Resources
        jobs = batch_v1.list_namespaced_job(name).items
        cronjobs = batch_v1.list_namespaced_cron_job(name).items
        
        # Networking Resources
        net_policies = net_v1.list_namespaced_network_policy(name).items
        ingresses = net_v1.list_namespaced_ingress(name).items

        # Build Summary Row
        row = {
            "Namespace": name,
            "Status": ns.status.phase,
            "Deployments": len(deployments),
            "StatefulSets": len(statefulsets),
            "DaemonSets": len(daemonsets),
            "Pods": len(pods),
            "Jobs": len(jobs),
            "CronJobs": len(cronjobs),
            "PVCs": len(pvcs),
            "NetworkPolicies": len(net_policies),
            "Ingress": len(ingresses),
            "Services": len(services),
            "ConfigMaps": len(configmaps),
            "Secrets": len(secrets)
        }
        inventory.append(row)

    return inventory

def save_report(data):
    # CSV Report
    df = pd.DataFrame(data)
    df.to_csv("ns_inventory_summary.csv", index=False)
    
    # JSON Report
    with open("ns_inventory_summary.json", "w") as f:
        json.dump(data, f, indent=4)
        
    print("\n--- Summary Report Generated ---")
    print("Files: ns_inventory_summary.csv, ns_inventory_summary.json")

if __name__ == "__main__":
    data = get_namespace_inventory()
    save_report(data)
