import csv
import json
import os
import pandas as pd
from kubernetes import client, config

# --- HELPER: RESOURCE NORMALIZATION ---
def parse_resource(value, res_type):
    """Converts K8s strings (500m, 1Gi) into integers. Returns -1 if undefined."""
    if not value or value == "0": return -1 
    value = str(value).lower()
    try:
        if res_type == "cpu":
            if value.endswith("m"): return int(value[:-1])
            return int(float(value) * 1000)
        if res_type == "mem":
            # Conversion factors to MiB
            units = {"ki": 1/1024, "mi": 1, "gi": 1024, "ti": 1024*1024}
            for u, mult in units.items():
                if value.endswith(u): return int(float(value[:-len(u)]) * mult)
            return int(float(value))
    except: return -1
    return -1

def get_pvc_details(k8s_core, namespace, vols):
    """Checks PVC count and determines if storage is shared (RWX)."""
    pvc_claims = [v.persistent_volume_claim.claim_name for v in vols if v.persistent_volume_claim]
    pvc_count = len(pvc_claims)
    if pvc_count == 0: return 0, "None"
    
    modes = set()
    try:
        for name in pvc_claims:
            pvc = k8s_core.read_namespaced_persistent_volume_claim(name, namespace)
            if pvc.spec.access_modes:
                modes.update(pvc.spec.access_modes)
    except: return pvc_count, "Unknown"
    
    complexity = "RWX" if "ReadWriteMany" in modes else "RWO"
    return pvc_count, complexity

def get_exposure_details(k8s_core, k8s_net, custom_api, ns, labels):
    """Discovers Services, Ingresses, or OCP Routes targeting this workload."""
    if not labels: return "None", "Internal", "No"
    
    found_services = []
    exposure_types = []
    is_ext = "No"

    try:
        all_svcs = k8s_core.list_namespaced_service(ns).items
        for svc in all_svcs:
            if svc.spec.selector and all(labels.get(k) == v for k, v in svc.spec.selector.items()):
                found_services.append(svc.metadata.name)
                exposure_types.append(svc.spec.type)
                if svc.spec.type in ["LoadBalancer", "NodePort"]: is_ext = "Yes"

        if found_services:
            ings = k8s_net.list_namespaced_ingress(ns).items
            for ing in ings:
                for rule in (ing.spec.rules or []):
                    for path in (rule.http.paths or []):
                        if path.backend.service and path.backend.service.name in found_services:
                            is_ext = "Yes"; exposure_types.append("Ingress")
            
            try:
                routes = custom_api.list_namespaced_custom_object("route.openshift.io", "v1", ns, "routes")
                for r in routes.get('items', []):
                    if r.get('spec', {}).get('to', {}).get('name') in found_services:
                        is_ext = "Yes"; exposure_types.append("Route")
            except: pass
    except: pass

    svc_str = ", ".join(set(found_services)) if found_services else "None"
    type_str = ", ".join(set(exposure_types)) if exposure_types else "Internal"
    return svc_str, type_str, is_ext

def analyze_containers(pod_spec):
    inits = pod_spec.init_containers if pod_spec.init_containers else []
    containers = pod_spec.containers if pod_spec.containers else []
    return len(inits), (len(containers)-1 if len(containers)>1 else 0), (len(inits)+len(containers))

def process_pod_spec(type_name, item, pod_spec, hpas, vpas, core, net, custom, schedule="N/A"):
    meta = item.metadata
    pod_template_meta = getattr(item.spec, 'template', item).metadata if hasattr(item.spec, 'template') else meta
    primary = pod_spec.containers[0]
    
    # Analysis functions
    init_c, side_c, total_c = analyze_containers(pod_spec)
    pvc_count, storage_comp = get_pvc_details(core, meta.namespace, pod_spec.volumes or [])
    svc_names, exp_type, is_ext = get_exposure_details(core, net, custom, meta.namespace, meta.labels)
    
    # Resource Logic
    res = primary.resources
    r_cpu = parse_resource(res.requests.get("cpu") if res.requests else None, "cpu")
    l_cpu = parse_resource(res.limits.get("cpu") if res.limits else None, "cpu")
    
    # --- NEW: Memory Metrics ---
    r_mem = parse_resource(res.requests.get("memory") if res.requests else None, "mem")
    l_mem = parse_resource(res.limits.get("memory") if res.limits else None, "mem")

    return {
        "Kind": type_name,
        "Namespace": meta.namespace,
        "Name": meta.name,
        "Replicas": getattr(item.spec, 'replicas', 1),
        "Schedule": schedule,
        "CPU_Request_Milli": r_cpu,
        "CPU_Limit_Milli": l_cpu,
        "Mem_Request_MiB": r_mem,      # Added
        "Mem_Limit_MiB": l_mem,        # Added
        "Init_Containers": init_c,
        "Sidecars": side_c,
        "Total_Containers": total_c,
        "PVC_Count": pvc_count,
        "Storage_Complexity": storage_comp,
        "Services": svc_names,
        "Exposure_Type": exp_type,
        "Exposed_Externally": is_ext,
        "HPA_Enabled": "Yes" if any(h.spec.scale_target_ref.name == meta.name for h in hpas if h.metadata.namespace == meta.namespace) else "No",
        "VPA_Enabled": "Yes" if any(v.get('spec', {}).get('targetRef', {}).get('name') == meta.name for v in vpas if v.get('metadata', {}).get('namespace') == meta.namespace) else "No",
        "Node_Selector": "Yes" if pod_spec.node_selector else "No",
        "Affinity_Rules": "Yes" if pod_spec.affinity else "No",
        "Host_Network": "Yes" if pod_spec.host_network else "No",
        "Privileged": "Yes" if (primary.security_context and primary.security_context.privileged) else "No",
        "Liveness_Probe": "Yes" if primary.liveness_probe else "No",
        "Readiness_Probe": "Yes" if primary.readiness_probe else "No",
        "Additional_Networks": len([n for n in (pod_template_meta.annotations or {}).get("k8s.v1.cni.cncf.io/networks", "").split(",") if n.strip()]) if pod_template_meta.annotations else 0,
        "ConfigMap_Count": len([v for v in (pod_spec.volumes or []) if v.config_map]),
        "Secret_Count": len([v for v in (pod_spec.volumes or []) if v.secret])
    }

def fetch_all_workloads():
    config.load_kube_config()
    core, apps, batch, net, custom = client.CoreV1Api(), client.AppsV1Api(), client.BatchV1Api(), client.NetworkingV1Api(), client.CustomObjectsApi()
    
    print("🔍 Fetching Global Configs (HPA/VPA)...")
    hpas = client.AutoscalingV1Api().list_horizontal_pod_autoscaler_for_all_namespaces().items
    vpas = []
    try: vpas = custom.list_cluster_custom_object("autoscaling.k8s.io", "v1", "verticalpodautoscalers").get('items', [])
    except: pass

    all_data = []
    targets = [("Deployment", apps.list_deployment_for_all_namespaces), 
               ("StatefulSet", apps.list_stateful_set_for_all_namespaces),
               ("DaemonSet", apps.list_daemon_set_for_all_namespaces),
               ("Job", batch.list_job_for_all_namespaces)]

    for kind, func in targets:
        print(f"📦 Auditing {kind}s...")
        for item in func().items:
            all_data.append(process_pod_spec(kind, item, item.spec.template.spec, hpas, vpas, core, net, custom))

    print("📦 Auditing CronJobs...")
    for cj in batch.list_cron_job_for_all_namespaces().items:
        all_data.append(process_pod_spec("CronJob", cj, cj.spec.job_template.spec.template.spec, hpas, vpas, core, net, custom, schedule=cj.spec.schedule))

    return all_data

if __name__ == "__main__":
    try:
        results = fetch_all_workloads()
        df = pd.DataFrame(results)
        df.to_csv('k8s_workload_inventory.csv', index=False)
        with open('k8s_workload_inventory.json', 'w') as f:
            json.dump(results, f, indent=4)
        print(f"\n✅ SUCCESS: Audit complete. {len(results)} workloads analyzed.")
    except Exception as e:
        print(f"❌ Error: {e}")
