import os
import json
from pathlib import Path
import time
from typing import Dict, List, Tuple, Optional
import litellm
from dotenv import load_dotenv
from datetime import datetime


class AISystem:
    """
    A harness for benchmarking Large Language Models against a specific codebase.
    It handles API communication via LiteLLM, context loading, prompt engineering,
    error handling (retries/rate limits), and state persistence for resuming interrupted runs.
    """
    def __init__(self, model: str, provider: str):
        """
        Initializes the AI system, configuring the API provider and loading necessary credentials.

        Args:
            model (str): The specific model identifier (e.g., "gpt-4-turbo", "gemini-1.5-pro").
            provider (str): The API provider ("openai", "google", "ollama", "copilot-api").

        Raises:
            ValueError: If the provider is not supported.
        """
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
        """
        Reads the content of a specific target file from the codebase to serve as context.

        Args:
            codebase_path (str): The root directory of the codebase.
            target_file (str): The relative path to the file to be analyzed.

        Returns:
            str: A formatted string containing the file content or an error message if unreadable.
        """
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
        """
        Constructs the final prompt by combining the codebase context, system instructions,
        and the specific multiple-choice question.

        Args:
            benchmark_item (Dict): The dictionary containing the question and answer options.
            codebase_context (str): The text content of the target file.

        Returns:
            str: The fully assembled prompt string ready to be sent to the LLM.
        """
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
        prompt = context_prompt + "\n" + question_prompt
        return prompt

    def _call_litellm(self, prompt: str) -> Tuple[str, Optional[str]]:
        """
        Executes the API call using LiteLLM with robust error handling and retry logic.
        Handles RateLimits, 503 Overloads, and generic internal errors.

        Args:
            prompt (str): The text prompt to send to the model.

        Returns:
            Tuple[str, Optional[str]]: A tuple containing:
                - The response content (str), or empty string on failure.
                - An error message (str) if an error occurred, otherwise None.
        """
        max_retries = 5
        last_error = None
        wait_time = 60

        for attempt in range(max_retries):
            try:
                response = litellm.completion(
                    model=self.model,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    api_key=self.api_key,
                    api_base=self.api_base
                )
                return response.choices[0].message.content.strip(), None

            except litellm.RateLimitError as e:
                print(f"Errore RateLimitError: Limite API raggiunto. Interruzione del processo. Riavvia lo script più tardi per continuare.")
                return "", f"RateLimitError: {e}"

            except litellm.InternalServerError as e:
                last_error = str(e)
                error_str = str(e).lower()
                if "503" in error_str or "unavailable" in error_str or "overloaded" in error_str:
                    if attempt < max_retries - 1:
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
        """
        Parses the raw text response from the AI to extract the selected option letter (A, B, C, or D).

        Args:
            ai_response (str): The raw output string from the LLM.

        Returns:
            str: The uppercase letter found (A/B/C/D), or an empty string if no valid letter is found.
        """
        if not ai_response: return ""
        ai_response = ai_response.upper().strip()
        if any(ai_response == f"RISPOSTA: {char}" for char in ['A', 'B', 'C', 'D']):
            return ai_response[-1] if ai_response[-1] in ['A', 'B', 'C', 'D'] else ""
        for char in ai_response:
            if char in ['A', 'B', 'C', 'D']:
                return char
        return ""

    def process_question(self, benchmark_item: Dict, codebase_path: str) -> Dict:
        """
        Orchestrates the processing of a single benchmark item.
        It handles context loading, prompt generation, API calls, and includes logic to
        retry if the model generates an excessively long response (>10 chars).

        Args:
            benchmark_item (Dict): The question data object.
            codebase_path (str): The root path to the codebase.

        Returns:
            Dict: A dictionary containing the detailed execution result (answer, correctness, errors).
        """
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
        
        max_len_retries = 5
        ai_response = ""
        cleaned_response = ""
        is_response_right = False
        call_error = None

        for i in range(max_len_retries):
            print(f"Invio domanda {benchmark_item['question_id']} al modello (Tentativo {i+1})...")
            
            ai_response, call_error = self._call_litellm(prompt)
            
            if call_error:
                error_msg = call_error
                break
            
            cleaned_response = ai_response.upper().strip()
            
            is_response_right = len(cleaned_response) <= 5 or any(cleaned_response == f"RISPOSTA: {char}" for char in ['A', 'B', 'C', 'D'])

            if is_response_right:
                break
            
            print(f"  -> Risposta troppo lunga ({len(cleaned_response)} char): '{cleaned_response[:20]}...'. Riprovo tra 60 secondi.")
            
            if i < max_len_retries - 1:
                prompt += "\n\n[SYSTEM MESSAGE]: La tua risposta precedente era troppo lunga. Rispondi SOLO con la lettera (A, B, C, o D)."

            time.sleep(60)

        if not is_response_right and not call_error:
            error_msg = "Risposta AI troppo lunga dopo più tentativi."
            ai_answer = ""
        else:
            ai_answer = self._extract_answer_letter(ai_response)
            
        is_correct = ai_answer == benchmark_item['correct_label'] if error_msg is None else False
        
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

    def _save_state(self, output_path: Path, current_run_summary: Dict):
        """
        Persists the current evaluation state to a JSON file.
        It reads existing history to ensure data for other models is not lost and updates/appends
        the current model's run data.

        Args:
            output_path (Path): The file path where results should be saved.
            current_run_summary (Dict): The data structure containing results and stats for the current run.
        """
        history = []
        if output_path.exists():
            try:
                with open(output_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        history = json.loads(content)
                        if not isinstance(history, list):
                            history = [history]
            except (json.JSONDecodeError, IOError) as e:
                print(f"Attenzione: impossibile leggere o decodificare il file storico {output_path}. Verrà creato un nuovo file. Errore: {e}")
                history = []

        run_found = False
        for i, run in enumerate(history):
            if run.get("model") == self.model and run.get("provider") == self.provider:
                history[i] = current_run_summary
                run_found = True
                break
        
        if not run_found:
            history.append(current_run_summary)
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"ERRORE CRITICO: Impossibile salvare lo stato in {output_path}. Errore: {e}")

    def evaluate_benchmark(self, benchmark_items: List[Dict], codebase_path: str, output_path: str = "ai_evaluation.json", wait_time: int = 60) -> Dict:
        """
        The main driver function that iterates through the benchmark items.
        Features:
        - Resumes from previous interruptions by checking processed IDs.
        - Groups results logically by template ID.
        - Calculates real-time statistics (accuracy per category).
        - Saves state after every single item to prevent data loss.

        Args:
            benchmark_items (List[Dict]): The list of questions to evaluate.
            codebase_path (str): The path to the codebase folder.
            output_path (str, optional): The JSON file for saving results. Defaults to "ai_evaluation.json".
            wait_time (int, optional): Seconds to wait between requests to avoid rate limits. Defaults to 60.

        Returns:
            Dict: The final summary of the evaluation run.
        """
        path = Path(output_path)
        processed_ids = set()
        current_run_summary = None

        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                    if not isinstance(history, list): history = [history]
                    
                    for run in history:
                        if run.get("model") == self.model and run.get("provider") == self.provider:
                            current_run_summary = run
                            for result_group in run.get("results", []):
                                for execution in result_group.get("executions", []):
                                    processed_ids.add(execution["execution_id"])
                            print(f"Trovata esecuzione precedente per {self.model}. Riprendendo... ({len(processed_ids)} items già processati)")
                            break
            except (json.JSONDecodeError, IOError) as e:
                print(f"Attenzione: file di output {path} corrotto o illeggibile. Si ricomincia da capo. Errore: {e}")

        if current_run_summary is None:
            print("Nessuna esecuzione precedente trovata per questo modello. Inizio una nuova valutazione.")
            current_run_summary = {
                "timestamp": datetime.now().isoformat(),
                "model": self.model,
                "provider": self.provider,
                "stats": {"correct": {}, "wrong": {}, "errors": 0, "accuracy": {}},
                "results": []
            }

        grouped_results = {res["template_id"]: res for res in current_run_summary["results"]}

        print(f"\n{'='*60}")
        print(f"Inizio valutazione su {len(benchmark_items)} item (Modello: {self.model})")
        print(f"{'='*60}\n")
        
        items_to_process = [item for item in benchmark_items if item['question_id'] not in processed_ids]
        if not items_to_process:
            print("Tutti gli item sono già stati processati. Nessuna nuova operazione da eseguire.")
        
        for i, item in enumerate(benchmark_items, 1):
            full_id = item['question_id']
            
            if full_id in processed_ids:
                print(f"\n[{i}/{len(benchmark_items)}] Item {full_id} già processato. Salto. \n")
                continue

            print(f"\n[{i}/{len(benchmark_items)}] Processando item {full_id}...")
            
            result = self.process_question(item, codebase_path)
            
            if result['error'] and "RateLimitError" in result['error']:
                print("Interruzione a causa di Rate Limit. I progressi sono stati salvati.")
                break

            logical_id = full_id.split('_')[0]
            if logical_id not in grouped_results:
                grouped_results[logical_id] = {
                    "template_id": logical_id,
                    "category": item['category'],
                    "question_template": item.get("question_template", item['question']),
                    "group_stats": {
                        "correct": 0,
                        "wrong": 0,
                        "errors": 0,
                        "total": 0,
                        "accuracy": 0.0
                    },
                    "executions": []
                }
            
            execution_detail = {
                "execution_id": full_id,
                "target_file": item.get('target_file'),
                "choosen_item": item.get('choosen_item'), 
                "ai_answer": result['ai_answer'],
                "ai_raw_response": result['ai_raw_response'],
                "correct_label": item['correct_label'],
                "is_correct": result['is_correct'],
                "error": result['error']
            }
            grouped_results[logical_id]["executions"].append(execution_detail)

            group_stats = grouped_results[logical_id]["group_stats"]
            group_stats["total"] += 1
            
            if result['error']:
                group_stats["errors"] += 1
            elif result['is_correct']:
                group_stats["correct"] += 1
            else:
                group_stats["wrong"] += 1
            
            valid_total = group_stats["total"] - group_stats["errors"]
            if valid_total > 0:
                group_stats["accuracy"] = round((group_stats["correct"] / valid_total) * 100, 2)
            else:
                group_stats["accuracy"] = 0.0
            
            current_run_summary["results"] = list(grouped_results.values())
            
            all_executions = [ex for group in current_run_summary["results"] for ex in group["executions"]]
            total_errors = sum(1 for ex in all_executions if ex["error"])
            
            stats_correct = {"spacing": 0, "naming": 0, "total": 0}
            stats_wrong = {"spacing": 0, "naming": 0, "total": 0}
            
            total_valid_for_accuracy = 0
            
            for group in current_run_summary["results"]:
                category = group.get("category")
                if category not in stats_correct:
                    stats_correct[category] = 0
                if category not in stats_wrong:
                    stats_wrong[category] = 0
                
                for ex in group["executions"]:
                    if not ex["error"]:
                        total_valid_for_accuracy += 1
                        if ex["is_correct"]:
                            stats_correct[category] += 1
                            stats_correct["total"] += 1
                        else:
                            stats_wrong[category] += 1
                            stats_wrong["total"] += 1

            valid_spacing = stats_correct.get("spacing", 0) + stats_wrong.get("spacing", 0)
            valid_naming = stats_correct.get("naming", 0) + stats_wrong.get("naming", 0)
            valid_total = stats_correct["total"] + stats_wrong["total"]

            accuracy_breakdown = {
                "spacing": round((stats_correct.get("spacing", 0) / valid_spacing) * 100, 2) if valid_spacing > 0 else 0.0,
                "naming": round((stats_correct.get("naming", 0) / valid_naming) * 100, 2) if valid_naming > 0 else 0.0,
                "total": round((stats_correct["total"] / valid_total) * 100, 2) if valid_total > 0 else 0.0
            }
            current_run_summary["stats"]["correct"] = stats_correct
            current_run_summary["stats"]["wrong"] = stats_wrong
            current_run_summary["stats"]["errors"] = total_errors
            current_run_summary["stats"]["accuracy"] = accuracy_breakdown
            current_run_summary["results"] = list(grouped_results.values())

            self._save_state(path, current_run_summary)
            print(f"  -> Progresso salvato in {path.name}")
            
            if not ("RateLimitError" in (result['error'] or "")):
                 time.sleep(wait_time)
        
        return current_run_summary