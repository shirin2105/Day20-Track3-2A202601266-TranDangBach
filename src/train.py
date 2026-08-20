import json
import os

import joblib
import mlflow
import mlflow.sklearn
import pandas as pd
import yaml
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, f1_score

F1_THRESHOLD = 0.65

def train(
    params: dict,
    data_path: str = "data/train_batch1.csv",
    eval_path: str = "data/holdout.csv",
) -> float:
    """
    Huấn luyện mô hình và ghi nhận kết quả vào MLflow.
    Trả về:
        f1 (float): điểm F1 của lớp dương trên tập holdout
    """
    # TODO 1: Đọc dữ liệu từ data_path và dữ liệu đánh giá từ eval_path.
    df_train = pd.read_csv(data_path)
    df_eval = pd.read_csv(eval_path)

    # TODO 2: Tách đặc trưng và nhãn.
    X_train = df_train.drop(columns=["target"])
    y_train = df_train["target"]
    
    X_eval = df_eval.drop(columns=["target"])
    y_eval = df_eval["target"]

    with mlflow.start_run():
        # TODO 3: Ghi nhận siêu tham số.
        mlflow.log_params(params)

        # TODO 4: Khởi tạo và huấn luyện GradientBoostingClassifier.
        model = GradientBoostingClassifier(**params, random_state=42)
        model.fit(X_train, y_train)

        # TODO 5: Dự đoán trên holdout và tính chỉ số.
        preds = model.predict(X_eval)
        f1 = f1_score(y_eval, preds)
        acc = accuracy_score(y_eval, preds)

        # TODO 6: Ghi nhận chỉ số vào MLflow.
        mlflow.log_metric("f1_score", f1)
        mlflow.log_metric("accuracy", acc)
        mlflow.sklearn.log_model(model, "model")

        # TODO 7: In kết quả.
        print(f"F1: {f1:.4f} | Accuracy: {acc:.4f}")

        # TODO 8: Lưu metrics ra outputs/report.json (GitHub Actions sẽ đọc file này).
        os.makedirs("outputs", exist_ok=True)
        with open("outputs/report.json", "w") as f:
            json.dump({"f1_score": f1, "accuracy": acc}, f)

        # TODO 9: Lưu mô hình ra models/model.joblib (sẽ được upload lên cloud storage).
        os.makedirs("models", exist_ok=True)
        joblib.dump(model, "models/model.joblib")

        # TODO 10: Trả về f1
        return float(f1)

if __name__ == "__main__":
    with open("params.yaml") as f:
        params = yaml.safe_load(f)
    train(params)
