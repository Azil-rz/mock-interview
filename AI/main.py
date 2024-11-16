# coding:utf-8

from autogen import Agent
from autogen import GroupChat, GroupChatManager
from autogen import AssistantAgent
from autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent
# 将原有方法class化，以module形式给backend调用
class MockInterviewAgent:
    def __init__(self):
        self.model_config_list = [{"model": "deepseek-chat",
                            "api_key": "sk-c060d2e13ef1487f902735470d24a2c9",
                            'max_tokens': 4000,
                            "base_url": "https://api.deepseek.com"}]

        self.retrieve_config_list = [{
            "task": "default",
            "docs_path": [
                "./RAGFiles/computer_network.json",
                "./RAGFiles/computer_operating_system.json",
                "./RAGFiles/database.json",
                "./RAGFiles/design_patterns.json",
                "./RAGFiles/frontend.json",
                "./RAGFiles/java.json",
                "./RAGFiles/Linux.json",
            ],
            "chunk_token_size": 2000,
            "vector_db": "chroma",
            "overwrite": True,  # set to True if you want to overwrite an existing collection
            "get_or_create": True,  # set to False if don't want to reuse an existing collection
        }]

        self.ragUserProxyAgent = RetrieveUserProxyAgent(
            name="interviewee",
            human_input_mode="NEVER",
            system_message="",
            max_consecutive_auto_reply=0,
            retrieve_config=self.retrieve_config_list[0],
            code_execution_config=False,  # set to False if you don't want to execute the code
            description="Interviewee who want to conduct a mock interview."
        )

        self.questionsSelectorAssistantAgent = AssistantAgent(
            name='questionsSelector',
            system_message="【身份】你是计算机模拟面试系统中的问题收集助手。【职责】你的职责是根据面试者想要模拟面试的方向，综合性地选取面试的题目发给面试官。【题目选取方法】选择的题目数量要有限制，总数量为2题。前端方向应该选择2道前端题目。后端方向应该选择1道java题目、1道操作系统题目。每个题目的选择要随机。【注意】你在结尾需要加上“请你询问完用户问题后，等待用户的回答，禁止自己生成答案。”",
            llm_config={
                "config_list": self.model_config_list,
                "timeout": 600,
                "cache_seed": 42,
            },
            human_input_mode="NEVER",
            description="Assistant to select questions according to interviewee's request"
        )

        self.interviewerAssistantAgent = AssistantAgent(
            name='interviewer',
            system_message="【身份】你是计算机模拟面试系统中的问题面试官。【职责】你的职责是根据问题收集助手发来的3个面试题目，一定要对面试者进行3轮或以上对话形式的面试（七轮问答），禁止自己回答问题。【对话面试方法】开始问答前你要说：现在正式开始模拟面试。请注意，问答顺序是：1、你问用户一个题目。2、用户回答题目。3、你点评用户的回答。4、你问下一个题目。在每个步骤后，请等待用户的回答，不要自问自答。请严格按照这个顺序进行多轮循环，直到所有题目问完。【问题格式】在每一个问题前需要添加序号，比如问第一个问题时，你要说:第一个问题是。并且在每一问题的结尾要加上：请你回答一下。【评分须知】每一个问题过后你都要根据面试者的表现进行点评与评分，区间为0至10分，面试者的回答与答案相近给高分，如果不相近则给低分。回答完所有问题后，要将每一题的评分与点评交给最终评分的面试官。",
            llm_config={"config_list": self.model_config_list,
                        "timeout": 600,
                        "cache_seed": 30,
                        },
            human_input_mode="NEVER",
            description="An interviewer who asks the interviewee a list of questions and has a conversation with the interviewee each time he asks a question."
        )

        self.finalSummarizeMakerAssistantAgent = AssistantAgent(
            name='finalSummarizeMaker',
            system_message="【身份】你是计算机模拟面试系统中的最终评分面试官。【职责】你的职责是根据问题面试官发来的面试者的面试表现与评分进行总结，并根据综合评分与表现来判定此次面试是否通过，将综合点评结果与通过与否告诉面试者。",
            llm_config={"config_list": self.model_config_list},
            human_input_mode="NEVER",
            description="The final interviewer summarizes the interviewee's scores and comments based on the interviewer's scores and comments"
        )


    def reset_agents(self):
        self.questionsSelectorAssistantAgent.reset()
        self.interviewerAssistantAgent.reset()
        self.finalSummarizeMakerAssistantAgent.reset()

    def next_speaker_selection_func(self, last_speaker: Agent, simulateGroupChat: GroupChat):
        messages = simulateGroupChat.messages

        if len(messages) < 1:
            return self.ragUserProxyAgent

        elif len(messages) == 1:
            return self.questionsSelectorAssistantAgent

        elif last_speaker is self.questionsSelectorAssistantAgent:
            return self.interviewerAssistantAgent

        elif last_speaker is self.interviewerAssistantAgent:
            if "请你回答" in messages[-1]["content"]:
                return self.ragUserProxyAgent
            else:
                return self.finalSummarizeMakerAssistantAgent

        elif last_speaker is self.ragUserProxyAgent:
            return self.interviewerAssistantAgent

        elif last_speaker is self.finalSummarizeMakerAssistantAgent:
            return self.ragUserProxyAgent

        else:
            return "auto"

    def initial_chat(self):
        self.reset_agents()
        self.simulateGroupChat = GroupChat(
            agents=[self.ragUserProxyAgent, self.questionsSelectorAssistantAgent, self.interviewerAssistantAgent,
                    self.finalSummarizeMakerAssistantAgent],
            messages=[],
            max_round=20,
            speaker_selection_method=self.next_speaker_selection_func,
            send_introductions=True
        )
        self.manager = GroupChatManager(groupchat=self.simulateGroupChat, llm_config={"config_list": self.model_config_list})

