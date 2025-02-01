import asyncio, os
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base import TaskResult
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
from configparser import ConfigParser
import ast, time

cfg = ConfigParser()
cfg.read("config.ini",encoding="utf-8")

os.environ['OPENAI_API_KEY'] = cfg.get("openai", "api_key")

def get_llm_client(agent_name):
    print("TEST", agent_name,  cfg.get(agent_name, "llm_type"), cfg.get(agent_name, "model"))
    if cfg.get(agent_name, "llm_type") == "openai":
        # 初始化 OpenAI 客戶端
        llm_client = OpenAIChatCompletionClient(
            model=cfg.get(agent_name, "model"),
            llm_config={
                    "cache_seed": 43,  # 更改 cache_seed 以進行不同的試驗
                    "temperature": cfg.getint("openai", "temperature"),  # 設定生成文本的隨機性
                    "timeout": cfg.getint("openai", "timeout"),    # 設定請求的超時時間
                    "max_tokens": cfg.getint("openai", "max_tokens"),  # 設定生成文本的最大字數
                }
            )
    elif cfg.get(agent_name, "llm_type") == "ollama":
        # 初始化本地客戶端
        llm_client = OpenAIChatCompletionClient(
            model=cfg.get(agent_name, "model"),
            #model="erwan2/DeepSeek-R1-Distill-Qwen-14B",
            api_key=cfg.get("ollama", "api_key"),  # 本地運行不需要 API 金鑰
            base_url=cfg.get("ollama", "base_url"),  # 本地服務的 URL
            model_capabilities={
                "json_output": False,  # 不支持 JSON 輸出
                "vision": False,       # 不支持視覺功能
                "function_calling": True,  # 支持函數調用
            },
            llm_config={
                    "cache_seed": 43,  # 更改 cache_seed 以進行不同的試驗
                    "temperature": cfg.getint("ollama","temperature"),  # 設定生成文本的隨機性
                    "timeout": cfg.getint("ollama","timeout"),    # 設定請求的超時時間
                    "max_tokens": cfg.getint("ollama","max_tokens"),  # 設定生成文本的最大字數
                }
        )

    return llm_client

# 主異步函數
async def main():
    # user_question = input("請輸入您的問題: ")  # 用戶輸入問題的提示

    # agent_proposer: 生成多個初始候選方案
    print(cfg.get("proposer", "llm_type"))
    agent_proposer = AssistantAgent(
        "agent_proposer", 
        model_client=get_llm_client("proposer"), 
        system_message=cfg.get("proposer","system_message")
        )
    
    # agent_evaluator: 評估候選方案並給予分數
    agent_evaluator = AssistantAgent(
        "agent_evaluator", 
        model_client=get_llm_client("evaluator"), 
        system_message=cfg.get("evaluator","system_message")
        )
    
    # agent_selector: 選定最佳方案
    agent_selector = AssistantAgent(
        "agent_selector", 
        model_client=get_llm_client("selector"), 
        system_message=cfg.get("selector","system_message")
        )
    
    # 設定終止條件
    termination_condition = TextMentionTermination("APPROVE")
    # 創建一個回合制團隊聊天
    team = RoundRobinGroupChat(
        [agent_proposer, agent_evaluator], 
        termination_condition=termination_condition, 
        max_turns=cfg.getint("global", "max_turns")
        )

    # 初始化歷史記錄
    history_proposer = []
    history_evaluator = []
    final_candidates = []  # 儲存最終候選方案
    i = 0

    # 開始團隊聊天的異步運行
    async for message in team.run_stream(task=cfg.get("global","user_question")):
        
        # 檢查消息是否為 TaskResult 類型
        if isinstance(message, TaskResult):
            print("Stop Reason:", message.stop_reason)  # 打印停止原因
            break

        # 獲取消息的來源、內容、類型和模型使用情況
        agent_namme = getattr(message, "source", None)
        response_content = getattr(message, "content", None)
        msg_type = getattr(message, "type", None)
        models_usage = getattr(message, "models_usage", None)

        print("")
        # 根據消息來源打印相應的內容
        if agent_namme == 'user':
            print("[任務開始]__________________________")
            print(response_content)
            
        elif agent_namme == 'agent_proposer':
            print(f"[{agent_namme}]__________________________")
            print(response_content)
            history_proposer.append(response_content)  # 保存 agent01 的歷史記錄
            final_candidates = response_content  # 更新最終候選方案
            
        elif agent_namme == 'agent_evaluator':
            print(f"[{agent_namme}]__________________________")
            print(response_content)
            history_evaluator.append(response_content)  # 保存 agent02 的歷史記錄
        
        # 檢查 agent02 是否核可方案
        if "APPROVE" in response_content and agent_namme == 'agent_evaluator':
            print("")
            print(f"{agent_namme} 已經核可這些方案!")
            break

    # 如果找到候選方案，繼續處理
    if len(final_candidates) > 0:   
        best_solution = await agent_selector.run(task=final_candidates)  # 獲取最佳方案
        
        # 提取 agent03 的回應內容
        if isinstance(best_solution, TaskResult):
            for msg in best_solution.messages:
                if msg.source.startswith('agent_selector'):
                    final_content = msg.content
                    print("")
                    print(f"[agent_selector]__________________________")
                    print(final_content)  # 打印最佳方案的內容
                    break
    
    else:
        print("No final_candidates found")  # 如果沒有找到候選方案

# 程式入口
if __name__ == "__main__":
    asyncio.run(main())  # 執行主函數