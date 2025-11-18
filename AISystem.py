import os
import json
from pathlib import Path
import time
from typing import Dict, List, Tuple, Optional # Aggiunto Tuple e Optional
from DataClassesDefiner import Question, BenchmarkItem
import litellm
from dotenv import load_dotenv
from datetime import datetime


class AISystem:
    
    def __init__(self, model: str, provider: str):
        self.model = model
        self.provider = provider.lower()
        self.env_file = "keys.env"
        load_dotenv(self.env_file)

        if self.provider == "openai":
            self.api_key = os.getenv("OPENAI_API_KEY")
            self.api_base = None
        elif self.provider == "google":
            self.api_key = os.getenv("GEMINI_API_KEY")
            self.api_base = None
        elif self.provider == "ollama":
            self.api_key = None
            self.api_base = "http://localhost:11434"
        elif self.provider == "copilot-api":
            self.api_key = None
            self.api_base = "http://localhost:4141/v1"
        else:
            raise ValueError(f"Provider sconosciuto: {provider}")

        print(f"Sistema AI inizializzato con modello: {self.model} (provider: {self.provider})")

    def _load_specific_file_context(self, codebase_path: str, target_file: str) -> str:
        full_path = Path(codebase_path) / target_file
        context = "=== CODEBASE ===\n\n"
        if not full_path.exists():
            return f"{context}--- File: {target_file} ---\nERRORE: File non trovato.\n\n"
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                context += f"--- File: {target_file} ---\n{content}\n\n"
        except Exception as e:
            context += f"--- File: {target_file} ---\nERRORE: Impossibile leggere il file. {e}\n\n"
        return context

    def _create_prompt(self, benchmark_item: Dict, codebase_context: str):
        context_prompt = f"""{codebase_context}
        === ISTRUZIONI ===
        Analizza attentamente la codebase fornita sopra e rispondi alla seguente domanda.
        IMPORTANTE: Devi rispondere SOLO con la lettera corrispondente alla risposta corretta (A, B, C, o D).
        Non aggiungere spiegazioni, commenti o altro testo. Solo la lettera."""

        question_prompt = f"""=== DOMANDA ===
        {benchmark_item['question']}
        === OPZIONI DI RISPOSTA ===
        """
        for answer in benchmark_item['answers']:
            question_prompt += f"{answer['label']}) {answer['text']}\n"
        question_prompt += "\nRisposta:"
        return {"prompt": question_prompt, "context": context_prompt}

    def _call_litellm(self, prompt: str, context: str) -> Tuple[str, Optional[str]]:
        """
        Effettua la chiamata API.
        Restituisce: (contenuto_risposta, messaggio_errore)
        """
        max_retries = 5  
        base_wait_time = 5 
        last_error = None

        for attempt in range(max_retries):
            try:
                response = litellm.completion(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": context},
                        {"role": "user", "content": prompt}
                    ],
                    api_key=self.api_key,
                    api_base=self.api_base
                )
                # Successo: Ritorna il contenuto e Nessun errore
                return response.choices[0].message.content.strip(), None

            except litellm.InternalServerError as e:
                last_error = str(e)
                error_str = str(e).lower()
                if "503" in error_str or "unavailable" in error_str or "overloaded" in error_str:
                    if attempt < max_retries - 1:
                        wait_time = base_wait_time * (2 ** attempt) 
                        print(f"Errore 503 (Overload). Riprovo tra {wait_time}s... (Tentativo {attempt + 2}/{max_retries})")
                        time.sleep(wait_time)
                    else:
                        print(f"Errore 503. Tentativi esauriti.")
                        return "", f"503 Overloaded (Max retries reached): {e}"
                else:
                    print(f"Errore InternalServerError: {e}")
                    return "", f"InternalServerError: {e}"

            except Exception as e:
                print(f"Errore generico LiteLLM: {e}")
                return "", f"Generic Error: {e}"

        return "", f"Unknown Error (Loop finished): {last_error}"

    def _extract_answer_letter(self, ai_response: str) -> str:
        if not ai_response: return ""
        ai_response = ai_response.upper().strip()
        for char in ai_response:
            if char in ['A', 'B', 'C', 'D']:
                return char
        return ""

    def process_question(self, benchmark_item: Dict, codebase_path: str) -> Dict:
        """Processa una domanda e salva eventuali errori."""
        target_file = benchmark_item.get('target_file')
        error_msg = None
        
        if not target_file:
            error_msg = "Missing 'target_file' in benchmark item"
            print(f"[ERRORE] {error_msg}")
            codebase_context = ""
        else:
            print(f"Caricamento file specifico: {target_file}...")
            codebase_context = self._load_specific_file_context(codebase_path, target_file)
        
        prompt = self._create_prompt(benchmark_item, codebase_context)
        print(f"Invio domanda {benchmark_item['question_id']} al modello {self.model} ({self.provider})...")
        
        ai_response, call_error = self._call_litellm(prompt["prompt"], prompt["context"])
        
        if call_error:
            error_msg = call_error
            
        ai_answer = self._extract_answer_letter(ai_response)
        is_correct = ai_answer == benchmark_item['correct_label']
        
        result = {
            "question_id": benchmark_item['question_id'],
            "category": benchmark_item['category'],
            "question": benchmark_item['question'],
            "correct_label": benchmark_item['correct_label'],
            "ai_answer": ai_answer,
            "ai_raw_response": ai_response,
            "is_correct": is_correct,
            "error": error_msg
        }
        
        status_icon = '✓' if is_correct else '✗'
        if error_msg: status_icon = '!'
            
        print(f"Risposta AI: {ai_answer} | Corretta: {benchmark_item['correct_label']} | Esito: {status_icon}")
        if error_msg:
            print(f"  -> Errore rilevato: {error_msg}")
            
        return result

    def evaluate_benchmark(self, benchmark_items: List[Dict], codebase_path: str, output_path: str = "ai_evaluation.json", wait_time: int = 10) -> Dict:
        """Valuta il modello e salva statistiche sugli errori."""
        results = []
        correct_count = {
            "spacing": 0,
            "naming": 0,
            "total": 0
        }
        wrong_count = {
            "spacing": 0,
            "naming": 0,
            "total": 0
        }
        error_count = 0
        
        print(f"\n{'='*60}")
        print(f"Inizio valutazione su {len(benchmark_items)} domande")
        print(f"{'='*60}\n")
        
        for i, item in enumerate(benchmark_items, 1):
            print(f"\n[{i}/{len(benchmark_items)}] Processando domanda {item['question_id']}...")
            result = self.process_question(item, codebase_path)
            results.append(result)
            
            if result['is_correct']:
                correct_count[result['category']] += 1
            else:
                wrong_count[result['category']] += 1
            
            if result['error']:
                error_count += 1
                
            time.sleep(wait_time)

        total_correct = correct_count["spacing"] + correct_count["naming"]
        total_wrong = wrong_count["spacing"] + wrong_count["naming"]
        correct_count['total'] = total_correct
        wrong_count['total'] = total_wrong

        accuracy = (total_correct) / len(benchmark_items) * 100 if benchmark_items else 0
        
        current_summary = {
            "timestamp": datetime.now().isoformat(),
            "model": self.model,
            "provider": self.provider,
            "total_questions": len(benchmark_items),
            "correct_answers": correct_count,
            "wrong_answers": wrong_count,
            "execution_errors": error_count,
            "accuracy": round(accuracy, 2),
            "results": results 
        }

        if output_path:
            history = []
            path = Path(output_path)

            if path.exists():
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:
                            loaded_data = json.loads(content)
                            if isinstance(loaded_data, list):
                                history = loaded_data
                            elif isinstance(loaded_data, dict):
                                history = [loaded_data]
                except Exception as e:
                    print(f"Errore leggendo lo storico: {e}")

            history.append(current_summary)

            try:
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(history, f, indent=2, ensure_ascii=False)
                print(f"\nRisultati salvati in {output_path}")
            except Exception as e:
                print(f"Errore durante il salvataggio: {e}")

        print(f"\n{'='*60}")
        print(f"RIEPILOGO VALUTAZIONE CORRENTE")
        print(f"{'='*60}")
        print(f"Modello: {self.model} ({self.provider})")
        print(f"Domande totali: {len(benchmark_items)}")
        print(f"Risposte corrette: {total_correct}")
        print(f"Risposte errate: {total_wrong}")
        print(f"Errori di esecuzione: {error_count}")
        print(f"Accuratezza: {accuracy:.2f}%")
        print(f"{'='*60}\n")
        
        return current_summary