# Backup & Restore Setup (Minikube)

## 1. Deploy Minio (S3-compatible storage)
```sh
kubectl apply -f minio-deployment.yaml
```
- Minio will be available on NodePort 30000. Access Key: `minio`, Secret Key: `minio123`.
- Create a bucket (e.g., `velero`) via Minio UI or mc CLI.

## 2. Deploy Velero prerequisites
```sh
kubectl apply -f velero-deployment.yaml
kubectl apply -f minio-credentials-secret.yaml
```

## 3. Install Velero (CLI)
Download Velero CLI from https://github.com/vmware-tanzu/velero/releases and run:
```sh
velero install \
  --provider aws \
  --plugins velero/velero-plugin-for-aws:v1.8.0 \
  --bucket <bucket-name> \
  --secret-file ./minio-credentials-secret.yaml \
  --use-volume-snapshots=false \
  --backup-location-config region=minio,s3ForcePathStyle="true",s3Url=http://192.168.49.2:30000 \
  --namespace velero
```

## 4. Example Backup/Restore
```sh
kubectl apply -f backup.yaml
kubectl apply -f restore.yaml
kubectl apply -f schedule.yaml
```

## 5. Clean up
```sh
kubectl delete -f .
```

---
- Adjust resource requests/limits as needed for your environment.
- For AWS, update provider/bucket/credentials accordingly.
