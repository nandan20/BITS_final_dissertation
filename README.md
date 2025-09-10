# NextGen Kubernetes Security, Backup, Cost, and AI Monitoring Platform

## Overview
This project provides a modular, production-ready Kubernetes platform integrating:
- **Security Scanning** (Trivy Operator)
- **Backup & Disaster Recovery** (Velero, Minio/S3)
- **Cost Monitoring** (OpenCost, Prometheus, Grafana)
- **AI/ML Monitoring** (Custom Python Exporters)

It is designed for easy deployment on Minikube, EKS, or any CNCF-compliant Kubernetes cluster. The stack is packaged for reproducibility and extensibility, with all manifests, Helm charts, and custom resources included.

---

## Architecture
```
┌────────────┐   ┌────────────┐   ┌────────────┐   ┌────────────┐
│  Trivy     │   │  Velero    │   │ OpenCost   │   │  Exporters │
│  Operator  │   │+Minio/S3   │   │+Prometheus │   │ (AI/CRD)   │
└─────┬──────┘   └─────┬──────┘   └─────┬──────┘   └─────┬──────┘
	│                │                │                │
	└─────► Kubernetes Cluster ◄──────┘                │
		(CRDs, Workloads, RBAC)                      │
			  │                                    │
			  └──────────────► Grafana ◄───────────┘
```

---

## Features
- **Automated Security Scanning**: Trivy Operator scans workloads and nodes for vulnerabilities, exposes results as CRDs and Prometheus metrics.
- **Backup & Restore**: Velero automates backup/restore of cluster resources and volumes, with Minio/S3 as the storage backend.
- **Cost Monitoring**: OpenCost and Prometheus collect and expose cost metrics, visualized in Grafana dashboards.
- **AI/ML Monitoring**: Custom Python exporters push AI/ML metrics to Prometheus for advanced monitoring and alerting.
- **Modular Deployment**: Deploy components independently or as a full stack using Helm or Kustomize.

---

## Prerequisites
- Kubernetes cluster (Minikube, EKS, or compatible)
- `kubectl` (v1.22+)
- `helm` (v3+)
- `docker` (for building custom images)
- `kubectl-slice` (for splitting large YAMLs, optional)
- Python 3.8+ (for exporters)
- Access to S3/Minio bucket (for Velero)

---

## Quick Start

### 1. Clone the Repository
```sh
git clone https://github.com/nandan20/NextGen-k8s-Platform.git
cd NextGen-k8s-Platform/security-scan-v1
```

### 2. Create Required Namespaces
```sh
kubectl create namespace monitoring
kubectl create namespace velero
kubectl create namespace opencost
# Add more as needed
```

### 3. Deploy Minio (S3-compatible storage for Velero)
```sh
kubectl apply -f backup_restore/minio-deployment.yaml
# Access Minio UI on NodePort 30000, login with minio/minio123
# Create a bucket (e.g., velero) via UI or mc CLI
```

### 4. Deploy Velero and Prerequisites
```sh
kubectl apply -f backup_restore/velero-deployment.yaml
kubectl apply -f backup_restore/minio-credentials-secret.yaml
```

### 5. Install Velero CLI (for backup/restore)
Download from https://github.com/vmware-tanzu/velero/releases and run:
```sh
velero install \
	--provider aws \
	--plugins velero/velero-plugin-for-aws:v1.8.0 \
	--bucket <bucket-name> \
	--secret-file ./backup_restore/minio-credentials-secret.yaml \
	--use-volume-snapshots=false \
	--backup-location-config region=minio,s3ForcePathStyle="true",s3Url=http://<minio-service-ip>:30000 \
	--namespace velero
```

### 6. Deploy Trivy Operator (Security)
```sh
kubectl apply -f trivy/securitysummary-crd.yaml
kubectl apply -f trivy/rbac-populator.yaml
kubectl apply -f trivy/servicemonitor.yaml
# Deploy Trivy Operator (see official docs for latest manifests)
```

### 7. Deploy OpenCost (Cost Monitoring)
```sh
kubectl apply -f cost-monitoring/opencost-deployment.yaml
kubectl label namespace opencost trivy-monitoring=enabled
kubectl apply -f cost-monitoring/opencost-servicemonitor.yaml
# Or use Helm:
helm repo add opencost https://opencost.github.io/opencost-helm-chart
helm install opencost opencost/opencost -f cost-monitoring/values.yaml
```

### 8. Deploy Prometheus & Grafana
```sh
kubectl apply -f monitoring/prometheus-rule.yaml
kubectl apply -f monitoring/grafana-dashboard.json
# Or use Helm for Prometheus/Grafana stack
```

### 9. Deploy Custom Exporters (CRD & AI/ML)

#### a. CRD Exporter
```sh
cd crd-exporter
pip install -r requirements.txt
python exporter.py
# Or build and run as Docker (see below)
```

#### b. AI Prediction Exporter
```sh
cd ai-prediction
pip install -r requirements.txt
python train_and_serve_model.py  # Train and serve Flask API
cd exporter
pip install -r requirements.txt
python prediction_exporter.py
# Or build and run as Docker:
docker build -t ai-prediction-exporter .
docker run --network=host ai-prediction-exporter
```

#### c. Deploy Exporters on Kubernetes
Use the provided deployment YAMLs in `crd-exporter/k8s/` and `ai-prediction/exporter/`.
```sh
kubectl apply -f crd-exporter/k8s/deployment.yaml
kubectl apply -f crd-exporter/k8s/rbac.yaml
kubectl apply -f ai-prediction/exporter/deployment.yaml
kubectl apply -f ai-prediction/exporter/service.yaml
kubectl apply -f ai-prediction/exporter/servicemonitor.yaml
```

### 10. Expose Metrics to Prometheus
- Ensure all exporters have a `ServiceMonitor` or `PodMonitor` for Prometheus scraping.
- Example ServiceMonitor: `trivy/servicemonitor.yaml`, `ai-prediction/exporter/servicemonitor.yaml`.

### 11. Deploy Full Stack with Helm or Kustomize (Optional)

#### a. Helm
```sh
cd nextgen-stack-helm
helm dependency update
helm install nextgen-stack . -f values.yaml
```

#### b. Kustomize
```sh
cd nextgen-stack-kustomize
kustomize build . | kubectl apply -f -
```

### 12. Example Backup/Restore with Velero
```sh
kubectl apply -f backup_restore/backup.yaml
kubectl apply -f backup_restore/restore.yaml
kubectl apply -f backup_restore/schedule.yaml
```

---

---

## Usage
- Access Grafana: `kubectl -n monitoring port-forward svc/kps-grafana 3000:80`
- Default dashboards: Security, Cost, Backup, AI/ML metrics
- Trigger backups/restores via Velero CLI or UI
- Review security scan results in Trivy CRDs and Grafana panels
- Monitor cost and AI metrics in real time

---

## Customization
- Edit `values.yaml` in each component directory for custom config
- Add/modify Grafana dashboards in `monitoring/`
- Extend Python exporters for new AI/ML metrics
- Use Helm/Kustomize for advanced deployment scenarios

---

## Troubleshooting
- **Pods not starting**: Check `kubectl get pods -A` and describe for errors
- **No metrics in Grafana**: Ensure Prometheus targets are up and exporters are running
- **Backup/restore issues**: Check Velero logs and S3/Minio connectivity
- **CRD errors**: Ensure all CRDs are applied before deploying operators

---

## References & Further Reading
- [Trivy Operator](https://aquasecurity.github.io/trivy-operator/)
- [Velero](https://velero.io/docs/)
- [OpenCost](https://www.opencost.io/docs/)
- [Prometheus](https://prometheus.io/docs/)
- [Grafana](https://grafana.com/docs/)
- [Kubernetes](https://kubernetes.io/docs/)

---

## License
This project is for academic and demonstration purposes. See individual component licenses for details.
