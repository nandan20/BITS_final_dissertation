from flask import Flask, Response
from prometheus_client import Gauge, generate_latest, CollectorRegistry, CONTENT_TYPE_LATEST
from kubernetes import client, config
from collections import defaultdict
import os

app = Flask(__name__)

# Load Kubernetes config
config.load_incluster_config()
k8s = client.CustomObjectsApi()

# Namespace for SecuritySummaryReport
CUSTOM_NAMESPACE = os.getenv("TARGET_NAMESPACE", "trivy-system")

# Register Prometheus metrics
registry = CollectorRegistry()

# === SecuritySummaryReport (custom CRD) ===
high_cve = Gauge('high_severity_cves', 'High severity CVEs', registry=registry)
critical_cve = Gauge('critical_severity_cves', 'Critical severity CVEs', registry=registry)
medium_cve = Gauge('medium_severity_cves', 'Medium severity CVEs', registry=registry)
low_cve = Gauge('low_severity_cves', 'Low severity CVEs', registry=registry)
unknown_cve = Gauge('unknown_severity_cves', 'Unknown severity CVEs', registry=registry)
total_cve = Gauge('total_cves', 'Total CVEs', registry=registry)

# === ConfigAuditReports ===
config_critical = Gauge('configaudit_critical_count', 'ConfigAudit Critical', ['name', 'namespace'], registry=registry)
config_high = Gauge('configaudit_high_count', 'ConfigAudit High', ['name', 'namespace'], registry=registry)
config_medium = Gauge('configaudit_medium_count', 'ConfigAudit Medium', ['name', 'namespace'], registry=registry)
config_low = Gauge('configaudit_low_count', 'ConfigAudit Low', ['name', 'namespace'], registry=registry)

# === RbacAssessmentReports ===
rbac_danger = Gauge('rbac_dangerous_rules', 'RBAC Dangerous Rules', ['name', 'namespace'], registry=registry)
rbac_warn = Gauge('rbac_warnings', 'RBAC Warnings', ['name', 'namespace'], registry=registry)
rbac_advice = Gauge('rbac_advice', 'RBAC Advice', ['name', 'namespace'], registry=registry)

# === ClusterRbacAssessmentReports ===
clusterrbac_danger = Gauge('clusterrbac_dangerous_rules', 'Cluster RBAC Dangerous Rules', registry=registry)
clusterrbac_warn = Gauge('clusterrbac_warnings', 'Cluster RBAC Warnings', registry=registry)
clusterrbac_advice = Gauge('clusterrbac_advice', 'Cluster RBAC Advice', registry=registry)

# === VulnerabilityReports (per-namespace, use exported_namespace label) ===
vuln_critical_total = Gauge('vuln_critical_total', 'Critical CVEs from VulnerabilityReports per namespace', ['exported_namespace'], registry=registry)
vuln_high_total = Gauge('vuln_high_total', 'High CVEs from VulnerabilityReports per namespace', ['exported_namespace'], registry=registry)
vuln_medium_total = Gauge('vuln_medium_total', 'Medium CVEs from VulnerabilityReports per namespace', ['exported_namespace'], registry=registry)
vuln_low_total = Gauge('vuln_low_total', 'Low CVEs from VulnerabilityReports per namespace', ['exported_namespace'], registry=registry)
vuln_unknown_total = Gauge('vuln_unknown_total', 'Unknown CVEs from VulnerabilityReports per namespace', ['exported_namespace'], registry=registry)

# === VulnerabilityReports (per workload) ===
vuln_workload_critical = Gauge('vuln_critical_per_workload', 'Critical CVEs per workload', ['namespace', 'workload'], registry=registry)
vuln_workload_high = Gauge('vuln_high_per_workload', 'High CVEs per workload', ['namespace', 'workload'], registry=registry)
vuln_workload_medium = Gauge('vuln_medium_per_workload', 'Medium CVEs per workload', ['namespace', 'workload'], registry=registry)
vuln_workload_low = Gauge('vuln_low_per_workload', 'Low CVEs per workload', ['namespace', 'workload'], registry=registry)
vuln_workload_unknown = Gauge('vuln_unknown_per_workload', 'Unknown CVEs per workload', ['namespace', 'workload'], registry=registry)

@app.route("/metrics")
def metrics():
    try:
        # === 1. SecuritySummaryReport ===
        summary = k8s.get_namespaced_custom_object(
            group="secscan.bits.io",
            version="v1",
            namespace=CUSTOM_NAMESPACE,
            plural="securitysummaryreports",
            name=f"{CUSTOM_NAMESPACE}-summary"
        )
        spec = summary.get("spec", {})
        high_cve.set(spec.get("highSeverityCount", 0))
        critical_cve.set(spec.get("criticalSeverityCount", 0))
        medium_cve.set(spec.get("mediumSeverityCount", 0))
        low_cve.set(spec.get("lowSeverityCount", 0))
        unknown_cve.set(spec.get("unknownSeverityCount", 0))
        total_cve.set(spec.get("totalCount", 0))

        # === 2. ConfigAuditReports ===
        configs = k8s.list_cluster_custom_object(
            group="aquasecurity.github.io", version="v1alpha1", plural="configauditreports"
        )
        config_critical.clear()
        config_high.clear()
        config_medium.clear()
        config_low.clear()
        for item in configs.get("items", []):
            meta = item["metadata"]
            name = meta["name"]
            ns = meta.get("namespace", "default")
            summary = item.get("report", {}).get("summary", {})
            config_critical.labels(name=name, namespace=ns).set(summary.get("criticalCount", 0))
            config_high.labels(name=name, namespace=ns).set(summary.get("highCount", 0))
            config_medium.labels(name=name, namespace=ns).set(summary.get("mediumCount", 0))
            config_low.labels(name=name, namespace=ns).set(summary.get("lowCount", 0))

        # === 3. RbacAssessmentReports ===
        rbac = k8s.list_cluster_custom_object(
            group="aquasecurity.github.io", version="v1alpha1", plural="rbacassessmentreports"
        )
        rbac_danger.clear()
        rbac_warn.clear()
        rbac_advice.clear()
        for item in rbac.get("items", []):
            meta = item["metadata"]
            name = meta["name"]
            ns = meta.get("namespace", "default")
            report = item.get("report", {})
            rbac_danger.labels(name=name, namespace=ns).set(report.get("dangerousRules", 0))
            rbac_warn.labels(name=name, namespace=ns).set(report.get("warnings", 0))
            rbac_advice.labels(name=name, namespace=ns).set(report.get("advice", 0))

        # === 4. ClusterRbacAssessmentReports ===
        crbac = k8s.list_cluster_custom_object(
            group="aquasecurity.github.io", version="v1alpha1", plural="clusterrbacassessmentreports"
        )
        for item in crbac.get("items", []):
            report = item.get("report", {})
            clusterrbac_danger.set(report.get("dangerousRules", 0))
            clusterrbac_warn.set(report.get("warnings", 0))
            clusterrbac_advice.set(report.get("advice", 0))

        # === 5. VulnerabilityReports ===
        vulns = k8s.list_cluster_custom_object(
            group="aquasecurity.github.io", version="v1alpha1", plural="vulnerabilityreports"
        )

        vuln_critical_total.clear()
        vuln_high_total.clear()
        vuln_medium_total.clear()
        vuln_low_total.clear()
        vuln_unknown_total.clear()
        vuln_workload_critical.clear()
        vuln_workload_high.clear()
        vuln_workload_medium.clear()
        vuln_workload_low.clear()
        vuln_workload_unknown.clear()

        ns_cves = defaultdict(lambda: {"critical": 0, "high": 0, "medium": 0, "low": 0, "unknown": 0})

        for item in vulns.get("items", []):
            meta = item.get("metadata", {})
            ns = meta.get("namespace", "default")
            name = meta.get("name", "unknown")
            summary = item.get("report", {}).get("summary", {})
            ns_cves[ns]["critical"] += summary.get("criticalCount", 0)
            ns_cves[ns]["high"] += summary.get("highCount", 0)
            ns_cves[ns]["medium"] += summary.get("mediumCount", 0)
            ns_cves[ns]["low"] += summary.get("lowCount", 0)
            ns_cves[ns]["unknown"] += summary.get("unknownCount", 0)

            vuln_workload_critical.labels(namespace=ns, workload=name).set(summary.get("criticalCount", 0))
            vuln_workload_high.labels(namespace=ns, workload=name).set(summary.get("highCount", 0))
            vuln_workload_medium.labels(namespace=ns, workload=name).set(summary.get("mediumCount", 0))
            vuln_workload_low.labels(namespace=ns, workload=name).set(summary.get("lowCount", 0))
            vuln_workload_unknown.labels(namespace=ns, workload=name).set(summary.get("unknownCount", 0))

        for ns, counts in ns_cves.items():
            vuln_critical_total.labels(exported_namespace=ns).set(counts["critical"])
            vuln_high_total.labels(exported_namespace=ns).set(counts["high"])
            vuln_medium_total.labels(exported_namespace=ns).set(counts["medium"])
            vuln_low_total.labels(exported_namespace=ns).set(counts["low"])
            vuln_unknown_total.labels(exported_namespace=ns).set(counts["unknown"])

        return Response(generate_latest(registry), mimetype=CONTENT_TYPE_LATEST)

    except Exception as e:
        return Response(f"# Error fetching metrics: {str(e)}\n", mimetype="text/plain")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
