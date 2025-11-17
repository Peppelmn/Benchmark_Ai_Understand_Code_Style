import json
from typing import Dict

from pyparsing import List
from DistractorGenerator import DistractorGenerator
from CodebaseAnalyzer import CodebaseAnalyzer
from Naming.NamingAnalyzer import NamingAnalyzer
from Spacing.SpacingAnalyzer import SpacingAnalyzer
from DataClassesDefiner import Answer, Question, BenchmarkItem
from Naming.NamingDistractorGenerator import NamingDistractorGenerator
from Spacing.SpacingDistractorGenerator import SpacingDistractorGenerator

class BenchmarkSystem:
    """Sistema principale per generare e gestire il benchmark"""
    
    def __init__(self, codebase_path: str):
        self.codebase_path = codebase_path
        
        # Registra i generatori di distrattori
        self.distractor_generators: Dict[str, DistractorGenerator] = {
            "naming": NamingDistractorGenerator(),
            "spacing": SpacingDistractorGenerator(),
        }
    
    def process_question(self, question: Question) -> BenchmarkItem:
        """Processa una singola domanda e genera l'item completo"""
        
        correct_answer = Answer(question.correct_answer_value, True)
        
        #Genera distrattori
        generator = self.distractor_generators.get(question.category)
        if not generator:
            raise ValueError(f"Generator non trovato: {question.category}")
        
        distractors = generator.generate(correct_answer, question)
        
        #Crea l'item completo
        return BenchmarkItem(
            question=question,
            correct_answer=correct_answer,
            distractors=distractors
        )
    
    def generate_benchmark(self, questions: List[Question], output_path: str = None) -> List[Dict]:
        """Genera il benchmark completo"""
        benchmark_items = []
        
        for question in questions:
            try:
                item = self.process_question(question)
                benchmark_items.append(item.to_dict())
            except Exception as e:
                print(f"Errore processando domanda {question.id}: {e}")
        
        # Salva su file se richiesto
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(benchmark_items, f, indent=2, ensure_ascii=False)
        
        return benchmark_items
    
    def get_benchmark_items(self, benchmark_path: str) -> List[Dict]:
        """Carica gli item del benchmark da un file JSON"""
        with open(benchmark_path, 'r', encoding='utf-8') as f:
            benchmark_items = json.load(f)
        return benchmark_items