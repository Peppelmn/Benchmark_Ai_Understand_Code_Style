import os
import warnings
from AISystem.AISystem import AISystem
from Benchmark.BenchmarkSystem import BenchmarkSystem
from AnswerDataset.DatasetGenerator import DatasetGenerator
from Codebase.GitHubLoader import GitHubLoader
import subprocess
import platform
import time
import os
import socket
from AnswerDistribution.DistributionAnalyzer import DistributionAnalyzer

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
    dataset_path = os.path.join(os.path.dirname(__file__), "AnswerDataset", "master_dataset.json")
    bencmark_path = os.path.join(os.path.dirname(__file__), "Benchmark", "benchmark.json")
    distribution_report_path = os.path.join(os.path.dirname(__file__), "AnswerDistribution", "answer_distribution_report.json")

    loader = GitHubLoader()
    loader.download_repositories(query="language:python stars:>10", limit=50, max_size_mb=200)

    dataset_generator = DatasetGenerator(codebase_path=codebase_path)
    dataset_generator.generate_dataset(output_path=dataset_path)

    distribution_analyzer = DistributionAnalyzer(dataset_path=dataset_path)
    distribution_analyzer.analyze(output_path=distribution_report_path)

    benchmark_generator = BenchmarkSystem(dataset_path=dataset_path)
    benchmark_generator.generate_benchmark(output_path=bencmark_path, target_count_per_question=10)
    
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
                # "gemini/gemini-2.5-flash",
                "gemini/gemini-3-flash-preview",
                # "gemini/gemini-2.5-pro",
            ]
        }

    for provider, models_list in models.items():
        provider_name = "copilot-api"
        if provider == "google":
            provider_name = "google"
        for model in models_list:
            evaluation_path = os.path.join(os.path.dirname(__file__), "AISystem", "EvaluationPerModel", f"{model.replace('/', '_')}_evaluation.json")

            ai_system = AISystem(model=model, provider=provider_name)

            items_to_evaluate = benchmark_generator.get_benchmark_items(bencmark_path)

            evaluation_results = ai_system.evaluate_benchmark(
                benchmark_items=items_to_evaluate,
                codebase_path=codebase_path,
                output_path=evaluation_path,
                wait_time=60
            )