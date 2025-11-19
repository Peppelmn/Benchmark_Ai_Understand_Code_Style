import os
import warnings
from AISystem import AISystem
from BenchmarkSystem import BenchmarkSystem
from QuestionDefiner import get_all_questions
from Spacing.SpacingAnalyzer import SpacingAnalyzer
from Naming.NamingAnalyzer import NamingAnalyzer
import subprocess
import platform
import time
import os
import socket

warnings.filterwarnings("ignore", category=SyntaxWarning)

def start_copilot_server():
    """
    Apre una NUOVA finestra di terminale ed esegue il server copilot-api.
    """

    def is_server_running(host="localhost", port=4141):
        """
        Controlla se c'è un servizio attivo sulla porta specificata.
        Restituisce True se la porta è aperta, False altrimenti.
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
    start_copilot_server()
    codebase_path = os.path.join(os.path.dirname(__file__), "Codebase", "black-main")
    spacingAnalyzer=SpacingAnalyzer(codebase_path=codebase_path)
    namingAnalyzer=NamingAnalyzer(codebase_path=codebase_path)
    try:
        questions = get_all_questions(spacingAnalyzer, namingAnalyzer)
        print(f"File saltati (Spacing): {spacingAnalyzer.parse_error_count} (a causa di errori di sintassi)")
        print(f"File saltati (Naming):  {namingAnalyzer.parse_error_count} (a causa di errori di sintassi)")
    except Exception as e:
        print(f"Errore durante la generazione delle domande: {e}")
        exit()

    system = BenchmarkSystem(codebase_path=codebase_path)

    # Genera il benchmark
    benchmark = system.generate_benchmark(questions, output_path="benchmark.json")

    models = {
        "openai" : 
            [
                "openai/gpt-4.1",
                # "openai/gpt-5-mini",
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
                # "gemini/gemini-2.5-pro",
            ]
        }

    for provider, models_list in models.items():
        for model in models_list:
            print(provider)
            ai_system = AISystem(model=model, provider="copilot-api" if provider!="google" else "google")
            evaluation_results = ai_system.evaluate_benchmark(
                benchmark_items=system.get_benchmark_items("benchmark.json"),
                codebase_path=codebase_path,
                output_path="ai_evaluation.json"
            )