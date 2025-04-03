# custom_agent.py

from langchain.agents import AgentExecutor

class CustomAgentExecutor(AgentExecutor):
    """
    Lớp CustomAgentExecutor kế thừa từ LangChain's AgentExecutor,
    giúp bạn mở rộng logic riêng nếu cần về sau.
    """

    @classmethod
    def from_agent_and_tools(cls, agent, tools, verbose=False):
        """
        Khởi tạo nhanh một executor với agent và tools.
        """
        return cls(agent=agent, tools=tools, verbose=verbose)
