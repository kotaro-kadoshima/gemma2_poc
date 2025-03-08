from flask import Flask, request, jsonify, send_from_directory
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import os
import signal

app = Flask(__name__)

# モデルとトークナイザーのロード
# 旧モデル
# model_name = "google/gemma-2b-it"
# 回答に5時間後に壊れたレスポンスがきた
# model_name = "google/gemma-2-2b"
# 日本語対応モデル
model_name = "google/gemma-2-2b-jpn-it"
hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")

print(f"{model_name} のロードを開始")
tokenizer = AutoTokenizer.from_pretrained(model_name, token=hf_token)
model = AutoModelForCausalLM.from_pretrained(
    model_name, torch_dtype=torch.float16, token=hf_token
)
model.eval()
print("モデルのロード完了")


def timeout_handler(signum, frame):
    raise TimeoutError("Processing request took too long!")


signal.signal(signal.SIGALRM, timeout_handler)


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_input = data.get("message")
    if not user_input:
        return jsonify({"error": "No input provided"}), 400

    # トークン化
    print("Processing input...")
    inputs = tokenizer(user_input, return_tensors="pt")
    # モデルによる生成
    with torch.no_grad():
        outputs = model.generate(**inputs, max_new_tokens=150)
    # テキスト化
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print("Generated response:", response)  # ここで生成したレスポンスを確認

    return jsonify({"response": response})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
