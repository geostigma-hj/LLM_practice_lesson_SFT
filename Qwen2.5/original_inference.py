# vllm_model.py
from vllm import LLM, SamplingParams
from transformers import AutoTokenizer
import os

# 自动下载模型时，指定使用modelscope; 否则，会从HuggingFace下载
os.environ['VLLM_USE_MODELSCOPE']='True'

def get_completion(prompts, model, tokenizer=None, max_tokens=512, temperature=0.8, top_p=0.95, max_model_len=2048):
    stop_token_ids = [151329, 151336, 151338]
    # 创建采样参数。temperature 控制生成文本的多样性，top_p 控制核心采样的概率
    sampling_params = SamplingParams(temperature=temperature, top_p=top_p, max_tokens=max_tokens, stop_token_ids=stop_token_ids)
    # 初始化 vLLM 推理引擎
    llm = LLM(model=model, tokenizer=tokenizer, max_model_len=max_model_len,trust_remote_code=True)
    outputs = llm.generate(prompts, sampling_params)
    return outputs


if __name__ == "__main__":    
    # 初始化 vLLM 推理引擎
    model='LLaMA-Factory/my_model/Qwen2.5-7B/Qwen/Qwen2.5-7B-Instruct' # 指定模型路径
    # model="qwen/Qwen2.5-7B-Instruct" # 指定模型名称，自动下载模型
    tokenizer = None
    stop_token_ids = [151329, 151336, 151338]
    # 创建采样参数。temperature 控制生成文本的多样性，top_p 控制核心采样的概率
    sampling_params = SamplingParams(temperature=1, top_p=1, max_tokens=512, stop_token_ids=stop_token_ids)
    llm = LLM(model=model, tokenizer=tokenizer, max_model_len=2048, trust_remote_code=True)
    
    text = [
            "概述一下丹东鼓乐的文化价值",
            "回族民间器乐属于什么类别的非遗文化？",
            "梳理一下回族宴席曲的历史脉络",
            "近年来壮族天琴艺术有哪些社会动态",
            "壮族天琴艺术是从哪里起源的？",
            "扬州玉雕的代表性传承人有哪些？"
        ]

    # 新增对话循环
    print("欢迎使用问答系统！输入 'exit' 退出对话")
    while True:
        user_input = input("\nUser：")
        if user_input.lower() in ['exit', 'quit']:
            break
            
        outputs = llm.generate([user_input], sampling_params)  # 直接使用已初始化的llm
        
        # 输出结果
        generated_text = outputs[0].outputs[0].text
        print(f"\nAssistant：{generated_text}\n")