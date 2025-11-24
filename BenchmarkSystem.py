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
    
    # In BenchmarkSystem.py

    def generate_benchmark(self, questions: List[Question], output_path: str = None) -> List[Dict]:
        benchmark_items = []
        
        for q in questions:
            # Iteriamo su tutti i file target trovati per questa domanda (es. 10)
            for i, target_file in enumerate(q.target_files):
                try:
                    # 1. Prepara il testo specifico
                    # Se c'è extra_data (es. nome variabile per N06), formattiamo la stringa
                    if q.extra_data:
                        formatted_text = q.text_template.format(q.extra_data[i])
                    else:
                        formatted_text = q.text_template

                    # 2. Risposta corretta specifica per questo file
                    correct_val = q.correct_answer_values[i]
                    correct_answer_obj = Answer(correct_val, True)

                    # 3. Generatore di Distrattori
                    # Creiamo un oggetto Question "proxy" temporaneo per il generatore
                    # (Il generatore si aspetta un oggetto Question con un ID per decidere la logica)
                    proxy_q = Question(
                        id=q.id, category=q.category, text_template=formatted_text,
                        target_files=[target_file], correct_answer_values=[correct_val]
                    )
                    
                    generator = self.distractor_generators.get(q.category)
                    distractors = generator.generate(correct_answer_obj, proxy_q)
                    
                    if distractors is None: distractors = [] # Safety check

                    # 4. Crea l'Item Finale
                    # Nota: Creiamo un nuovo oggetto Question "fisico" per questo singolo item
                    # così il to_dict funzionerà correttamente
                    single_file_q = Question(
                        id=f"{q.id}_{i+1}", # ID Univoco: S01_1, S01_2...
                        category=q.category,
                        text_template=formatted_text,
                        target_files=[target_file], # Lista di 1 elemento
                        correct_answer_values=[correct_val]
                    )

                    item = BenchmarkItem(
                        question=single_file_q,
                        correct_answer=correct_answer_obj,
                        distractors=distractors
                    )
                    
                    # Converti in dict e aggiungi alla lista
                    item_dict = item.to_dict()
                    # Sovrascriviamo target_file per essere sicuri che sia una stringa nel JSON finale
                    item_dict["target_file"] = target_file
                    item_dict["question_template"] = q.text_template.format("choosen_item") if q.extra_data else q.text_template
                    item_dict["choosen_item"] = q.extra_data[i] if q.extra_data else None
                    
                    benchmark_items.append(item_dict)

                except Exception as e:
                    print(f"Errore generando item {q.id}_{i+1}: {e}")

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(benchmark_items, f, indent=2, ensure_ascii=False)

        return benchmark_items
        
    def get_benchmark_items(self, benchmark_path: str) -> List[Dict]:
        """Carica gli item del benchmark da un file JSON"""
        with open(benchmark_path, 'r', encoding='utf-8') as f:
            benchmark_items = json.load(f)
        return benchmark_items