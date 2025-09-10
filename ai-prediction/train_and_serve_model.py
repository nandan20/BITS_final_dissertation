import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from joblib import dump, load
from flask import Flask, request, jsonify
import os

# 1. Load dummy data
df = pd.read_csv('dummy_backup_data.csv', parse_dates=['timestamp'])
df['hour'] = df['timestamp'].dt.hour

# 2. Feature selection and label
y = df['backup_failed']
X = df[['backup_duration', 'validation_errors', 'hour']]

# 3. Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 4. Train model
clf = RandomForestClassifier(n_estimators=10, random_state=42)
clf.fit(X_train, y_train)

# 5. Save model
dump(clf, 'backup_failure_predictor.joblib')

# 6. Evaluate
if len(X_test) > 0:
    y_pred = clf.predict(X_test)
    print('Validation accuracy:', accuracy_score(y_test, y_pred))

# 7. Real-time prediction API
app = Flask(__name__)
model = load('backup_failure_predictor.joblib')

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    features = [[
        data['backup_duration'],
        data['validation_errors'],
        data['hour']
    ]]
    prob = model.predict_proba(features)[0][1]
    pred = model.predict(features)[0]
    return jsonify({
        'failure_probability': float(prob),
        'predicted_failure': int(pred)
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)
