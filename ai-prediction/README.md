
# AI-based Backup Failure Prediction (Real-time)

## 1. Install dependencies
```sh
cd ai-prediction
pip install -r requirements.txt
```

## 2. Train and Serve the Model
```sh
python train_and_serve_model.py
```
- This will train a simple model on dummy data and start a Flask API at `http://localhost:5001/predict`.
- The server keeps running and can be queried for predictions.

## 3. Test Real-time Prediction
Send a POST request (e.g., with curl or Postman):
```sh
curl -X POST http://localhost:5001/predict \
  -H 'Content-Type: application/json' \
  -d '{"backup_duration": 120, "validation_errors": 0, "hour": 14}'
```
- Response will include `failure_probability` and `predicted_failure`.

## 4. Export Prediction as Prometheus Metric

### a. Build and run the exporter (locally or in Docker)
```sh
cd exporter
pip install -r requirements.txt
python prediction_exporter.py
# OR build and run with Docker:
docker build -t ai-prediction-exporter .
docker run --network=host ai-prediction-exporter
```


### b. Kubernetes deployment
1. Build and push your Docker image (already done: `ninandan/ai-prediction-exporter:latest`).
2. Deploy the exporter using the provided YAMLs:
  ```sh
  kubectl apply -f exporter/deployment.yaml
  kubectl apply -f exporter/service.yaml
  kubectl apply -f exporter/servicemonitor.yaml
  ```
3. Make sure Prometheus is scraping the exporter on port 8001.

## 5. Grafana Dashboard

- Import `exporter/grafana-dashboard.json` into Grafana.
- This dashboard visualizes the predicted backup failure probability as a stat and time series.

## 6. Validation
- The model prints validation accuracy after training.
- You can update `dummy_backup_data.csv` with real data as it becomes available.
- Test the full pipeline by:
  - Running the model API
  - Running the exporter
  - Checking Prometheus for the metric `ai_predicted_backup_failure_probability`
  - Viewing the Grafana dashboard
