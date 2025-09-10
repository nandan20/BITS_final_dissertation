import time
import requests
from prometheus_client import start_http_server, Gauge
import datetime

# Prometheus metric
failure_prob_gauge = Gauge('ai_predicted_backup_failure_probability', 'Predicted probability of backup failure')

# Dummy function: Replace with real logic to fetch latest backup job features
# In production, fetch from Prometheus or Kubernetes API

def get_latest_backup_features():
    # Example: simulate a backup job at 9am with high duration and errors
    now = datetime.datetime.now()
    return {
        "backup_duration": 170,
        "validation_errors": 2,
        "hour": now.hour
    }

def main():
    start_http_server(8001)  # Expose metrics at :8001/metrics
    while True:
        features = get_latest_backup_features()
        try:
            resp = requests.post("http://host.docker.internal:5001/predict", json=features, timeout=5)
            prob = resp.json()["failure_probability"]
            failure_prob_gauge.set(prob)
            print(f"Exported failure probability: {prob}")
        except Exception as e:
            print(f"Prediction or export failed: {e}")
        time.sleep(60)  # Update every minute

if __name__ == "__main__":
    main()
