from chatterbot.logic import LogicAdapter
from chatterbot.conversation import Statement

class MyLogicAdapter(LogicAdapter):
    eval = None
    listener = None
    botIns = None
    
    def __init__(self, chatbot, **kwargs):
        super().__init__(chatbot, **kwargs)
        self.botIns = kwargs.get("botIns")
        self.listener = kwargs.get("listener")

    def can_process(self, statement):
        # self.botIns.CrashReport("can_process", "MyLogicAdapter")
        for i in self.listener:
            words = i.get("content")
            for x in words:
                if x in statement.text:
                    self.botIns.CrashReport("process","MyLogicAdapter")
                    self.eval = i
                    return True
        return False
    
    def process(self, input_statement, additional_response_selection_parameters):
        text = self.botIns.execPlugin(self.eval.get("eval"))
        self.botIns.CrashReport(text, "MyLogicAdapter")
        response_statement = Statement(text=text, confidence=1)
        return response_statement