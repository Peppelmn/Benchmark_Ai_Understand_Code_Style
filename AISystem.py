import os
import json
from pathlib import Path
from typing import Dict, List
from DataClassesDefiner import Question, BenchmarkItem
import litellm
from dotenv import load_dotenv


class AISystem:
    
    def __init__(self, model: str, provider: str = "ollama"):
        """
        Inizializza il sistema AI.
        
        Args:
            model: Nome del modello da utilizzare (es. gpt-4, llama3, mistral, ecc.)
            provider: Provider del modello ("openai", "groq", "ollama")
        """
        self.model = model
        self.provider = provider.lower()
        self.env_file = "keys.env"

        # Carica variabili d'ambiente
        load_dotenv(self.env_file)

        # Configura in base al provider
        if self.provider == "openai":
            self.api_key = os.getenv("OPENAI_API_KEY")
            self.api_base = None

        elif self.provider == "groq":
            self.api_key = os.getenv("GROQ_API_KEY")
            self.api_base = None

        elif self.provider == "ollama":
            # Ollama gira in locale, quindi non serve API key
            self.api_key = None
            self.api_base = "http://localhost:11434"

        else:
            raise ValueError(f"Provider sconosciuto: {provider}")

        print(f"Sistema AI inizializzato con modello: {self.model} (provider: {self.provider})")
        if self.api_key:
            print(f"API Key caricata da {self.env_file}: ✓")
        else:
            print(f"Nessuna API Key necessaria per {self.provider.upper()}")

    def _load_codebase_context(self, codebase_path: str, max_files: int = 200) -> str:
        """Carica il contenuto della codebase come contesto per l'AI."""
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

    def _create_prompt(self, benchmark_item: Dict, codebase_context: str):
        """Crea il prompt per l'AI includendo la codebase e la domanda."""
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

    def _call_litellm(self, prompt: str, context: str) -> str:
        """Effettua la chiamata API usando LiteLLM."""
        try:
            response = litellm.completion(
                model=f"ollama/{self.model}" if self.provider == "ollama" else self.model,
                messages=[
                    {"role": "system", "content": context},
                    {"role": "user", "content": prompt}
                ],
                api_key=self.api_key,
                api_base=self.api_base  # Ollama
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Errore nella chiamata a LiteLLM: {e}")
            return ""

    def _extract_answer_letter(self, ai_response: str) -> str:
        """Estrae la lettera della risposta dal testo dell'AI."""
        ai_response = ai_response.upper().strip()
        for char in ai_response:
            if char in ['A', 'B', 'C', 'D']:
                return char
        return ""

    def process_question(self, benchmark_item: Dict, codebase_path: str) -> Dict:
        """Processa una singola domanda inviandola all'AI e valuta la risposta."""
        print(f"Caricamento codebase da {codebase_path}...")
        codebase_context = self._load_codebase_context(codebase_path)
        prompt = self._create_prompt(benchmark_item, codebase_context)
        print(f"Invio domanda {benchmark_item['question_id']} al modello {self.model} ({self.provider})...")
        ai_response = self._call_litellm(prompt["prompt"], prompt["context"])
        ai_answer = self._extract_answer_letter(ai_response)
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

    def evaluate_benchmark(self, benchmark_items: List[Dict], codebase_path: str, output_path: str = "ai_evaluation.json") -> Dict:
        """Valuta il modello su tutto il benchmark."""
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
        accuracy = (correct_count / len(benchmark_items)) * 100 if benchmark_items else 0
        evaluation_summary = {
            "model": self.model,
            "provider": self.provider,
            "total_questions": len(benchmark_items),
            "correct_answers": correct_count,
            "wrong_answers": len(benchmark_items) - correct_count,
            "accuracy": round(accuracy, 2),
            "results": results
        }
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(evaluation_summary, f, indent=2, ensure_ascii=False)
            print(f"\nRisultati salvati in {output_path}")
        print(f"\n{'='*60}")
        print(f"RIEPILOGO VALUTAZIONE")
        print(f"{'='*60}")
        print(f"Modello: {self.model} ({self.provider})")
        print(f"Domande totali: {len(benchmark_items)}")
        print(f"Risposte corrette: {correct_count}")
        print(f"Risposte errate: {len(benchmark_items) - correct_count}")
        print(f"Accuratezza: {accuracy:.2f}%")
        print(f"{'='*60}\n")
        return evaluation_summary
