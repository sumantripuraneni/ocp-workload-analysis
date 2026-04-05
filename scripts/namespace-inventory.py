import csv
import json
import pandas as pd
from kubernetes import client, config

def get_resource_quota_status(k8s_core, namespace):
    """Checks for ResourceQuotas in the namespace."""
    try:
        quotas = k8s_core.list_namespaced_resource_quota(namespace).items
        return "Yes" if len(quotas) > 0 else "No"
    except: return "No"

def get_egress_ip_count(k8s_custom, namespace):
    """Checks for Egress IPs (OVN-Kubernetes and OpenShift SDN)."""
    count = 0
    try:
        # Check OVN-Kubernetes EgressIPs (CRD)
        egress_ips = k8s_custom.list_cluster_custom_object("k8s.ovn.org", "v1", "egressips")
        for eip in egress_ips.get('items', []):
            if eip['metadata'].get('name') == namespace:
                count += len(eip.get('spec', {}).get('egressIPs', []))
        
        # Check OpenShift SDN NetNamespace (Legacy)
        try:
            net_ns = k8s_custom.get_cluster_custom_object("network.openshift.io", "v1", "netnamespaces", namespace)
            count += len(net_ns.get('egressIPs', []))
        except: pass
    except: pass
    return count

def get_ingress_route_count(k8s_net, k8s_custom, namespace):
    """Counts K8s Ingresses and OpenShift Routes."""
    count = 0
    try:
        # Standard Ingresses
        count += len(k8s_net.list_namespaced_ingress(namespace).items)
        # OpenShift Routes
        try:
            routes = k8s_custom.list_namespaced_custom_object("route.openshift.io", "v1", namespace, "routes")
            count += len(routes.get('items', []))
        except: pass
    except: pass
    return count

def fetch_namespace_inventory():
    config.load_kube_config()
    core = client.CoreV1Api()
    apps = client.AppsV1Api()
    batch = client.BatchV1Api()
    networking = client.NetworkingV1Api()
    custom = client.CustomObjectsApi()
    
    namespaces = core.list_namespace().items
    inventory = []

    print(f"📊 Auditing {len(namespaces)} Namespaces...")

    for ns in namespaces:
        name = ns.metadata.name
        
        # 1. Governance & Security Metrics
        res_quota = get_resource_quota_status(core, name)
        egress_count = get_egress_ip_count(custom, name)
        ingress_route_count = get_ingress_route_count(networking, custom, name)
        
        try:
            net_pol_count = len(networking.list_namespaced_network_policy(name).items)
        except: 
            net_pol_count = 0

        # 2. Aggregated Workload & Config Counts
        try:
            deploy_count = len(apps.list_namespaced_deployment(name).items)
            sts_count = len(apps.list_namespaced_stateful_set(name).items)
            ds_count = len(apps.list_namespaced_daemon_set(name).items)
            job_count = len(batch.list_namespaced_job(name).items)
            cj_count = len(batch.list_namespaced_cron_job(name).items)
            
            cm_count = len(core.list_namespaced_config_map(name).items)
            secret_count = len(core.list_namespaced_secret(name).items)
            
            pod_count = len(core.list_namespaced_pod(name).items)
            pvc_count = len(core.list_namespaced_persistent_volume_claim(name).items)
            svc_count = len(core.list_namespaced_service(name).items)
        except Exception:
            deploy_count = sts_count = ds_count = job_count = cj_count = 0
            cm_count = secret_count = pod_count = pvc_count = svc_count = 0

        inventory.append({
            "Namespace": name,
            "Status": ns.status.phase,
            "Resource_Quota": res_quota,
            "Network_Policy_Count": net_pol_count,
            "Egress_IP_Count": egress_count,
            "Ingress_Routes": ingress_route_count,
            "Deployments": deploy_count,
            "StatefulSets": sts_count,
            "DaemonSets": ds_count,
            "Jobs": job_count,
            "CronJobs": cj_count,
            "Total_Pods": pod_count,
            "Total_PVCs": pvc_count,
            "Total_Services": svc_count,
            "Total_ConfigMaps": cm_count,
            "Total_Secrets": secret_count,
            "Labels_Count": len(ns.metadata.labels) if ns.metadata.labels else 0,
            "Creation_Date": ns.metadata.creation_timestamp.strftime("%Y-%m-%d")
        })

    return inventory

if __name__ == "__main__":
    try:
        data = fetch_namespace_inventory()
        df = pd.DataFrame(data)
        
        # Save to CSV
        csv_file = 'k8s_namespace_inventory.csv'
        df.to_csv(csv_file, index=False)
        
        # Save to JSON
        json_file = 'k8s_namespace_inventory.json'
        with open(json_file, 'w') as f:
            json.dump(data, f, indent=4)
        
        print(f"\n✅ Audit Complete!")
        print(f"📂 CSV Saved: {csv_file}")
        print(f"📂 JSON Saved: {json_file}")
        print(f"📊 Total Namespaces Analyzed: {len(df)}")
        
    except Exception as e:
        print(f"❌ Critical Error: {e}")
