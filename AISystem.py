import os
import json
import requests
from pathlib import Path
from typing import Dict, List, Tuple
from DataClassesDefiner import Question, BenchmarkItem


class AISystem:
    
    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "llama3.1"):
        """
        Inizializza il sistema AI.
        
        Args:
            ollama_url: URL del server Ollama
            model: Nome del modello da utilizzare
        """
        self.ollama_url = ollama_url
        self.model = model
        self.api_endpoint = f"{ollama_url}/api/generate"
    
    def _load_codebase_context(self, codebase_path: str, max_files: int = 200) -> str:
        """
        Carica il contenuto della codebase come contesto per l'AI.
        
        Args:
            codebase_path: Path alla codebase
            max_files: Numero massimo di file da includere
            
        Returns:
            Stringa contenente il contenuto dei file Python
        """
        codebase = Path(codebase_path)
        python_files = list(codebase.rglob("*.py"))[:max_files]
        
        context = "=== CODEBASE ===\n\n"
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    relative_path = file_path.relative_to(codebase)
                    context += f"--- File: {relative_path} ---\n{content}\n\n"
            except Exception as e:
                print(f"Errore leggendo {file_path}: {e}")
        
        return context
    
    def _create_prompt(self, benchmark_item: Dict, codebase_context: str) -> str:
        """
        Crea il prompt per l'AI includendo la codebase e le istruzioni.
        
        Args:
            benchmark_item: Item del benchmark con domanda e risposte
            codebase_context: Contesto della codebase
            
        Returns:
            Prompt completo
        """
        prompt = f"""{codebase_context}

            === ISTRUZIONI ===
            Analizza attentamente la codebase fornita sopra e rispondi alla seguente domanda.

            IMPORTANTE: Devi rispondere SOLO con la lettera corrispondente alla risposta corretta (A, B, C, o D).
            Non aggiungere spiegazioni, commenti o altro testo. Solo la lettera.

            === DOMANDA ===
            {benchmark_item['question']}

            === OPZIONI DI RISPOSTA ===
            """
        
        for answer in benchmark_item['answers']:
            prompt += f"{answer['label']}) {answer['text']}\n"
        
        prompt += "\nRisposta:"
        
        return prompt
    
    def _call_ollama(self, prompt: str) -> str:
        """
        Effettua la chiamata API a Ollama.
        
        Args:
            prompt: Prompt da inviare
            
        Returns:
            Risposta dell'AI
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,  # Bassa temperatura per risposte più deterministiche
                "top_p": 0.9,
                "num_predict": 10  # Limitiamo la lunghezza della risposta
            }
        }
        
        try:
            response = requests.post(self.api_endpoint, json=payload, timeout=120)
            response.raise_for_status()
            result = response.json()
            return result.get('response', '').strip()
        except requests.exceptions.RequestException as e:
            print(f"Errore nella chiamata a Ollama: {e}")
            return ""
    
    def _extract_answer_letter(self, ai_response: str) -> str:
        """
        Estrae la lettera della risposta dal testo dell'AI.
        
        Args:
            ai_response: Risposta completa dell'AI
            
        Returns:
            Lettera della risposta (A, B, C, D) o stringa vuota
        """
        # Cerca la prima lettera A, B, C, o D nella risposta
        ai_response = ai_response.upper().strip()
        
        for char in ai_response:
            if char in ['A', 'B', 'C', 'D']:
                return char
        
        return ""
    
    def process_question(self, benchmark_item: Dict, codebase_path: str) -> Dict:
        """
        Processa una singola domanda inviandola all'AI e valutando la risposta.
        
        Args:
            benchmark_item: Item del benchmark generato
            codebase_path: Path alla codebase da analizzare
            
        Returns:
            Dizionario con i risultati della valutazione
        """
        # Carica il contesto della codebase
        print(f"Caricamento codebase da {codebase_path}...")
        codebase_context = self._load_codebase_context(codebase_path)
        
        # Crea il prompt
        prompt = self._create_prompt(benchmark_item, codebase_context)
        
        # Invia la domanda all'AI
        print(f"Invio domanda {benchmark_item['question_id']} all'AI...")
        ai_response = self._call_ollama(prompt)
        
        # Estrai la lettera della risposta
        ai_answer = self._extract_answer_letter(ai_response)
        
        # Verifica correttezza
        is_correct = ai_answer == benchmark_item['correct_label']
        
        result = {
            "question_id": benchmark_item['question_id'],
            "category": benchmark_item['category'],
            "question": benchmark_item['question'],
            "correct_label": benchmark_item['correct_label'],
            "ai_answer": ai_answer,
            "ai_raw_response": ai_response,
            "is_correct": is_correct
        }
        
        print(f"Risposta AI: {ai_answer} | Corretta: {benchmark_item['correct_label']} | Esito: {'✓' if is_correct else '✗'}")
        
        return result
    
    def evaluate_benchmark(self, benchmark_items: List[Dict], codebase_path: str, 
                          output_path: str = "ai_evaluation.json") -> Dict:
        """
        Valuta l'AI su tutto il benchmark.
        
        Args:
            benchmark_items: Lista di item del benchmark
            codebase_path: Path alla codebase
            output_path: Path dove salvare i risultati
            
        Returns:
            Dizionario con statistiche e risultati dettagliati
        """
        results = []
        correct_count = 0
        
        print(f"\n{'='*60}")
        print(f"Inizio valutazione su {len(benchmark_items)} domande")
        print(f"{'='*60}\n")
        
        for i, item in enumerate(benchmark_items, 1):
            print(f"\n[{i}/{len(benchmark_items)}] Processando domanda {item['question_id']}...")
            result = self.process_question(item, codebase_path)
            results.append(result)
            
            if result['is_correct']:
                correct_count += 1
        
        # Calcola statistiche
        accuracy = (correct_count / len(benchmark_items)) * 100 if benchmark_items else 0
        
        evaluation_summary = {
            "model": self.model,
            "total_questions": len(benchmark_items),
            "correct_answers": correct_count,
            "wrong_answers": len(benchmark_items) - correct_count,
            "accuracy": round(accuracy, 2),
            "results": results
        }
        
        # Salva risultati
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(evaluation_summary, f, indent=2, ensure_ascii=False)
            print(f"\nRisultati salvati in {output_path}")
        
        # Stampa riepilogo
        print(f"\n{'='*60}")
        print(f"RIEPILOGO VALUTAZIONE")
        print(f"{'='*60}")
        print(f"Modello: {self.model}")
        print(f"Domande totali: {len(benchmark_items)}")
        print(f"Risposte corrette: {correct_count}")
        print(f"Risposte errate: {len(benchmark_items) - correct_count}")
        print(f"Accuratezza: {accuracy:.2f}%")
        print(f"{'='*60}\n")
        
        return evaluation_summary