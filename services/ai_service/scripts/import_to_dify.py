import os
import requests
import time

# ================= 配置区 =================
DIFY_BASE_URL = "http://localhost/v1"   # 你本机 Dify 的 API 地址
API_KEY = "dataset-p7YeUvKFFIcWZASSRscF5JgX"          # 第一步获取的 API Key
DATASET_ID = "8beb32d6-25fc-4fac-ac04-28af9b05b23d"       # 第一步获取的 Dataset ID

TXT_DIR = r"D:\Python\xiaoyunote\services\ai_service\data\corpus\txt"
# =========================================

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

def import_txt_files():
    files = sorted([f for f in os.listdir(TXT_DIR) if f.endswith(".txt")])
    print(f"共发现 {len(files)} 个 TXT 文件，开始导入...")

    for idx, fname in enumerate(files, 1):
        fpath = os.path.join(TXT_DIR, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            text = f.read()

        # 用文件名（不含扩展名）作为文档名
        doc_name = os.path.splitext(fname)[0]

        payload = {
            "name": doc_name,
            "text": text,
            "indexing_technique": "high_quality",   # 高质量索引
            "process_rule": {
                "mode": "custom",
                "rules": {
                    "pre_processing_rules": [
                        {"id": "remove_extra_spaces", "enabled": True},
                        {"id": "remove_urls_emails", "enabled": True}
                    ],
                    "segmentation": {
                        "separator": "\n\n",
                        "max_tokens": 800,
                        "chunk_overlap": 50
                    }
                }
            }
        }

        url = f"{DIFY_BASE_URL}/datasets/{DATASET_ID}/document/create-by-text"
        resp = requests.post(url, json=payload, headers=headers, timeout=30)

        if resp.status_code == 200:
            data = resp.json()
            print(f"[{idx}/{len(files)}] ✅ {doc_name} 导入成功，batch: {data.get('batch', 'N/A')}")
        else:
            print(f"[{idx}/{len(files)}] ❌ {doc_name} 导入失败：{resp.status_code} {resp.text}")

        time.sleep(0.3)   # 轻微延迟，避免请求过密

    print("\n全部导入请求已发送。索引在后台异步进行，请稍后到知识库页面查看索引状态。")

if __name__ == "__main__":
    import_txt_files()