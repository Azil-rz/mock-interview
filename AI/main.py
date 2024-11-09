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
                "./RAGFiles/FrontEndQuestions.json",
                "./RAGFiles/ComputerNetworkQuestions.json",
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
            system_message="你是计算机模拟面试系统中的问题收集助手，你的职责是根据面试者想要模拟面试的方向，综合性地选取面试的题目发给面试官。记住，选择的题目数量要有限制，比如前端开发岗位只能选取一题前端相关的题目与一题计算机网络相关的题目。",
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
            system_message="你是计算机模拟面试系统中的问题面试官，你的职责是根据拿到的面试题目与面试者进行对话形式的面试。在每一个问题前需要添加序号，比如问第一个问题时，你要说:第一个问题是。并且在每一问题的结尾要加上：请你回答一下。在面试者回答完问题且回答与答案较为接近或一致时，你需要针对回答中错误的地方给出纠正，然后进行下一个问题的询问。如果与答案差别过大，你可以先不纠正，而是在当前问题上进行诱导回答，最多诱导两轮就要进行下一个问题的询问。每一个问题过后你都要根据面试者的表现进行点评与评分，区间为0至10分，面试者的回答与答案相近给高分，如果不相近则给低分。回答完所有问题后，要将每一题的评分与点评交给最终评分的面试官。",
            llm_config={"config_list": self.model_config_list},
            human_input_mode="NEVER",
            description="An interviewer who asks the interviewee a list of questions and has a conversation with the interviewee each time he asks a question."
        )

        self.finalSummarizeMakerAssistantAgent = AssistantAgent(
            name='finalSummarizeMaker',
            system_message="你是计算机模拟面试系统中的最终评分面试官。你的职责是根据问题面试官发来的面试者的面试表现与评分进行总结，并根据综合评分与表现来判定此次面试是否通过，将综合点评结果与通过与否告诉面试者。",
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
        # 去除这段初始化代码，在websocket链接建立成功后，从client端输入
        # await self.ragUserProxyAgent.a_initiate_chat(
        #     manager,
        #     message=self.ragUserProxyAgent.message_generator,
        #     problem="你好，我是这次的面试者，想进行前端方向的模拟面试。"
        # )
