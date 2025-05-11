from modelscope import snapshot_download

# 下载并保存模型
model_dir = snapshot_download('tiansz/bert-base-chinese', cache_dir="./bert-base-chinese", revision="master")