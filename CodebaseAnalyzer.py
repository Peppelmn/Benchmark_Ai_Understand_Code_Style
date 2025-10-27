from abc import abstractmethod
from pathlib import Path
from DataClassesDefiner import Question, Answer

class CodebaseAnalyzer:
    """Classe base per analizzatori di codebase"""
    
    def __init__(self, codebase_path: str):
        self.codebase_path = Path(codebase_path)
        self.python_files = list(self.codebase_path.rglob("*.py"))
    
    @abstractmethod
    def analyze(self, question: Question) -> Answer:
        """Analizza la codebase e trova la risposta corretta"""
        pass