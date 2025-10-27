from CodebaseAnalyzer import CodebaseAnalyzer
from DataClassesDefiner import Question, Answer

class NamingAnalyzer(CodebaseAnalyzer):
    """Analizza la codebase su aspetti di naming, trova la risposta corretta per le domande"""

    def analyze(self, question: Question) -> Answer:
        """Implementa l'analisi per la domanda di naming"""

        # Scorri le domande di naming e crei metodi specifici per ognuna per trovare la risposta corretta