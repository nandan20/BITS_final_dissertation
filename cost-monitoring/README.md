# Kubernetes Cost Monitoring & Optimization (OpenCost)

## Overview
This module integrates [OpenCost](https://www.opencost.io/) for Kubernetes cost monitoring. It works on Minikube and all major clouds.

---

## Steps

### 1. Deploy OpenCost

```sh
kubectl apply -f cost-monitoring/opencost-deployment.yaml
kubectl label namespace opencost trivy-monitoring=enabled
kubectl apply -f cost-monitoring/opencost-servicemonitor.yaml
