import csv
import json
import pandas as pd
from kubernetes import client, config

def get_resource_value(resource_dict, key, default="0"):
    if not resource_dict: return default
    return resource_dict.get(key, default)

def analyze_containers(pod_spec):
    """Returns counts and names for Init Containers and Sidecars."""
    init_info = pod_spec.init_containers if pod_spec.init_containers else []
    init_count = len(init_info)
    init_names = [c.name for c in init_info]

    all_containers = pod_spec.containers if pod_spec.containers else []
    sidecar_count = len(all_containers) - 1 if len(all_containers) > 1 else 0
    sidecar_names = [c.name for c in all_containers[1:]] if sidecar_count > 0 else []

    return init_count, init_names, sidecar_count, sidecar_names

def process_pod_spec(type_name, meta, pod_spec, extra_info=None):
    """Standardizes the extraction for all workload types."""
    init_count, init_names, sidecar_count, sidecar_names = analyze_containers(pod_spec)
    
    primary = pod_spec.containers[0]
    res = primary.resources
    lim = res.limits if res.limits else {}
    req = res.requests if res.requests else {}

    # Storage and Config counts
    vol_list = pod_spec.volumes if pod_spec.volumes else []
    
    data = {
        "Kind": type_name,
        "Namespace": meta.namespace,
        "Name": meta.name,
        "Schedule": extra_info if extra_info else "N/A", # Only for CronJobs
        "CPU_Limit": get_resource_value(lim, "cpu"),
        "Mem_Limit": get_resource_value(lim, "memory"),
        "Has_Init": "Yes" if init_count > 0 else "No",
        "Init_Names": ", ".join(init_names),
        "Has_Sidecars": "Yes" if sidecar_count > 0 else "No",
        "Sidecar_Names": ", ".join(sidecar_names),
        "PVC_Count": len([v for v in vol_list if v.persistent_volume_claim]),
        "ConfigMap_Count": len([v for v in vol_list if v.config_map]),
        "Secret_Count": len([v for v in vol_list if v.secret]),
        "Total_Containers": init_count + len(pod_spec.containers)
    }
    return data

def fetch_all_workloads():
    config.load_kube_config()
    apps_v1 = client.AppsV1Api()
    batch_v1 = client.BatchV1Api()
    
    all_data = []

    # 1. Standard Workloads (Deployments, StatefulSets, DaemonSets)
    workload_mappings = [
        ("Deployment", apps_v1.list_deployment_for_all_namespaces),
        ("StatefulSet", apps_v1.list_stateful_set_for_all_namespaces),
        ("DaemonSet", apps_v1.list_daemon_set_for_all_namespaces),
        ("Job", batch_v1.list_job_for_all_namespaces)
    ]

    for kind, func in workload_mappings:
        for item in func().items:
            pod_spec = item.spec.template.spec
            all_data.append(process_pod_spec(kind, item.metadata, pod_spec))

    # 2. CronJobs (Special Handling for nesting)
    cron_jobs = batch_v1.list_cron_job_for_all_namespaces().items
    for cj in cron_jobs:
        pod_spec = cj.spec.job_template.spec.template.spec
        all_data.append(process_pod_spec("CronJob", cj.metadata, pod_spec, extra_info=cj.spec.schedule))

    return all_data

if __name__ == "__main__":
    try:
        final_results = fetch_all_workloads()
        
        # Save CSV
        pd.DataFrame(final_results).to_csv('k8s_full_inventory.csv', index=False)
        
        # Save JSON
        with open('k8s_full_inventory.json', 'w') as f:
            json.dump(final_results, f, indent=4)
            
        print(f"Audit Successful. Captured {len(final_results)} total workloads (including CronJobs).")
    except Exception as e:
        print(f"Error: {e}")
