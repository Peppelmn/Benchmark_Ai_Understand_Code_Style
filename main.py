import os
import random
import warnings
from AISystem import AISystem
from BenchmarkSystem import BenchmarkSystem
from GitHubLoader import GitHubLoader
from QuestionDefiner import get_all_questions
from Spacing.SpacingAnalyzer import SpacingAnalyzer
from Naming.NamingAnalyzer import NamingAnalyzer
import subprocess
import platform
import time
import os
import socket
from pathlib import Path
from DistributionAnalyzer import DistributionAnalyzer

warnings.filterwarnings("ignore", category=SyntaxWarning)

def start_copilot_server():
    """
    Launches the Copilot API server in a new dedicated terminal window.
    It checks if the server is already running on the default port (4141) before attempting startup.
    """
    def is_server_running(host="localhost", port=4141):
        """
        Checks if a service is actively listening on the specified host and port.

        Args:
            host (str): The hostname to check. Defaults to "localhost".
            port (int): The port number to check. Defaults to 4141.

        Returns:
            bool: True if the connection is successful (server running), False otherwise.
        """
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            return False

    system = platform.system()
    command = "npx copilot-api@latest start"

    if is_server_running():
        print("Il server Copilot è già attivo.")
        return
    
    print(f"Avvio del server Copilot su {system}...")

    try:
        subprocess.Popen(f'start cmd /k "{command}"', shell=True)
    
        for _ in range(20):
            time.sleep(1)
            if is_server_running():
                print("\nServer Copilot avviato con successo.")
                return
            
        print("Il server Copilot non è riuscito ad avviarsi entro il tempo previsto.")

    except Exception as e:
        print(f"Errore nell'avvio automatico del server: {e}")
        print(f"Per favore esegui manualmente: {command}")

if __name__ == "__main__":
    codebase_path = os.path.join(os.path.dirname(__file__), "Codebase", "downloads")
    # start_copilot_server()
    # loader = GitHubLoader()
    # loader.download_repositories(query="language:python stars:>10", limit=100, max_size_mb=200)
    # distributionAnalyzer = DistributionAnalyzer()
    # distributionAnalyzer.analyze(output_path="answer_distribution_report.json")
    
    models = {
        "openai" : 
            [
                # "openai/gpt-4.1",
                # "openai/gpt-5.1",
                # "openai/gpt-3.5-turbo",
                # "openai/gpt-4o-mini",
                # "openai/gpt-4",
                # "openai/gpt-4o",
                # "openai/gpt-5.1",
                # "openai/gpt-5.1-codex",
                # "openai/gpt-5.1-codex-mini",
                # "openai/gpt-5-codex"
            ],
        "anthropic" : 
            [
                # "anthropic/claude-sonnet-4",
                # "anthropic/claude-sonnet-4.5",
                # "anthropic/claude-haiku-4.5"
            ],
        "google" : 
            [
                "gemini/gemini-2.5-flash",
                # "gemini/gemini-3.0-flash",
                # "gemini/gemini-2.5-pro",
            ]
        }

    for provider, models_list in models.items():
        provider_name = "copilot-api"
        if provider == "google":
            provider_name = "google"

        codebase_path = os.path.join(os.path.dirname(__file__), "Codebase", "downloads")
            
        for model in models_list:
            safe_model_name = model.replace('/', '_')
            
            bench_dir = Path("Benchmark_per_model")
            eval_dir = Path("Evaluation_per_model")
            
            bench_dir.mkdir(parents=True, exist_ok=True)
            eval_dir.mkdir(parents=True, exist_ok=True)

            benchmark_path = bench_dir / f"{safe_model_name}_benchmark.json"
            evaluation_path = eval_dir / f"{safe_model_name}_evaluation.json"
            
            benchmark_file = str(benchmark_path)
            evaluation_file = str(evaluation_path)
            
            max_token_per_minute = 115000 
            if model == "gemini/gemini-2.5-pro":
                max_token_per_minute = 125000 
            elif model == "gemini/gemini-2.5-flash":
                max_token_per_minute = 200000 
            elif model in ["openai/gpt-4o-mini", "openai/gpt-3.5-turbo"]:
                max_token_per_minute = 10000 

            system = BenchmarkSystem(codebase_path=codebase_path)

            if benchmark_path.exists():
                print(f"\nBenchmark trovato per {model}: '{benchmark_file}'.")
            else:
                print(f"\nCreazione NUOVO benchmark per {model}...")
                
                spacingAnalyzer = SpacingAnalyzer(codebase_path=codebase_path, max_token_limit=max_token_per_minute)
                namingAnalyzer = NamingAnalyzer(codebase_path=codebase_path, max_token_limit=max_token_per_minute)
                
                try:
                    questions = get_all_questions(spacingAnalyzer, namingAnalyzer)
                    print(f"\t->File scartati per errori di parsing Ast(Spacing): {spacingAnalyzer.parse_error_count}")
                    print(f"\t->File scartati per errori di parsing Ast(Naming):  {namingAnalyzer.parse_error_count}")
                except Exception as e:
                    print(f"Errore fatale durante la generazione delle domande: {e}")
                    exit()

                system.generate_benchmark(questions, output_path=benchmark_path)
                print(f"Benchmark salvato in '{benchmark_path}'")

            # print(f"Avvio valutazione AI per {model}...")
            
            # ai_system = AISystem(model=model, provider=provider_name)
            
            # items_to_evaluate = system.get_benchmark_items(benchmark_file)
            
            # evaluation_results = ai_system.evaluate_benchmark(
            #     benchmark_items=items_to_evaluate,
            #     codebase_path=codebase_path,
            #     output_path=evaluation_file,
            #     wait_time=60
            # )\