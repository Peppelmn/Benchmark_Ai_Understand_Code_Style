import json
import os
from collections import Counter

class DistributionAnalyzer:
    """
    Analyzes the distribution of correct answers (Ground Truth) by reading the pre-generated 'master_dataset.json'.
    It generates a unified statistical report, sorting questions by ID (S01->S13, N01->N09) and aggregating data
    from both static (single answer per file) and dynamic (sampled from raw data) question types.
    """
    
    def __init__(self, dataset_path: str):
        self.dataset_path = dataset_path

    def analyze(self, output_path: str = "answer_distribution_report.json"):
        """
        Executes the statistical analysis on the loaded dataset and saves the results to a JSON file.

        The method performs the following steps:
        1. Checks for the existence of the input dataset and the output path.
        2. Iterates through the dataset to accumulate raw data.
           - For **Static Questions** (e.g., S01, N01): Collects the single correct answer found in the file.
           - For **Dynamic Questions** (e.g., N05, S13): Aggregates all available raw samples (e.g., all snake_case names) found in the file.
        3. Calculates frequency distributions (counts and percentages) for all question types.
        4. Sorts the results logically: Spacing questions (S) first, followed by Naming questions (N), in numerical order.
        5. Exports the final formatted report to a JSON file.

        Args:
            output_path (str, optional): The file path where the analysis report will be saved. Defaults to "answer_distribution_report.json".

        Returns:
            None: The method writes directly to the file system and prints status messages to the console.
        """
        if os.path.exists(output_path):
            print(f"[INFO] Esiste già un report in {output_path}. Salto la generazione.\n")
            return

        if not os.path.exists(self.dataset_path):
            print(f"[ERRORE] Dataset non trovato: {self.dataset_path}\n")
            return

        try:
            with open(self.dataset_path, 'r', encoding='utf-8') as f:
                dataset = json.load(f)
        except Exception as e:
            print(f"[ERRORE] Impossibile leggere il dataset: {e}\n")
            return

        print(f"\nDataset caricato: {len(dataset)} file analizzati.\n")

        # --- 1. ACCUMULATORI ---
        # Usiamo un dizionario temporaneo per accumulare i dati grezzi prima del calcolo
        # key: question_id -> value: oggetto con contatori
        
        # Inizializziamo i contatori per le domande dinamiche
        # (Quelle statiche verranno aggiunte dinamicamente se trovate)
        dynamic_targets = ["N05", "N06", "N08", "S13"]
        accumulators = {
            qid: {"valid_files": 0, "samples": Counter(), "is_dynamic": True} 
            for qid in dynamic_targets
        }

        # Contenitore per le statiche (accumuliamo liste di valori)
        static_raw_values = {} 

        # --- 2. CICLO UNICO SUL DATASET ---
        for entry in dataset:
            answers = entry.get("answers", {})
            
            # A. Gestione Domande Statiche (S01-S12, N01-N04, N07, N09)
            for q_id, value in answers.items():
                if q_id.startswith("_") or q_id in dynamic_targets:
                    continue
                
                if q_id not in static_raw_values:
                    static_raw_values[q_id] = []
                
                # Convertiamo in stringa per poter fare il Counter, ma manteniamo la formattazione
                static_raw_values[q_id].append(str(value))

            # B. Gestione Domande Dinamiche (S13, N05, N06, N08)
            
            # N05 / N06 (Naming Samples)
            snakes = answers.get("_raw_names_snake") or []
            camels = answers.get("_raw_names_camel") or []
            pascals = answers.get("_raw_names_pascal") or []
            others = answers.get("_raw_names_other") or []
            
            has_names = (len(snakes) + len(camels) + len(pascals)) > 0
            
            if has_names:
                # N05: Distribuzione Convenzioni
                accumulators["N05"]["valid_files"] += 1
                accumulators["N05"]["samples"]["snake_case"] += len(snakes)
                accumulators["N05"]["samples"]["camelCase"] += len(camels)
                accumulators["N05"]["samples"]["PascalCase"] += len(pascals)
                
                # N06: Standard vs Non Standard
                accumulators["N06"]["valid_files"] += 1
                accumulators["N06"]["samples"]["standard"] += (len(snakes) + len(camels) + len(pascals))
                accumulators["N06"]["samples"]["non_standard"] += len(others)

            # N08 (Costanti)
            constants = answers.get("_raw_constants") or []
            if constants:
                accumulators["N08"]["valid_files"] += 1
                for c in constants:
                    val = "true" if "_" in c else "false"
                    accumulators["N08"]["samples"][val] += 1

            # S13 (Argument Strategies)
            strategies = answers.get("_raw_S13") or []
            if strategies:
                accumulators["S13"]["valid_files"] += 1
                for item in strategies:
                    strat = item.get("strategy", "unknown")
                    accumulators["S13"]["samples"][strat] += 1

        # --- 3. COSTRUZIONE REPORT UNIFICATO ---
        final_report_unsorted = {}

        # Processa Statiche
        for q_id, values in static_raw_values.items():
            total = len(values)
            counts = Counter(values)
            sorted_dist = sorted(counts.items(), key=lambda x: x[1], reverse=True)
            
            dist_dict = {
                val: f"{count} ({(count/total)*100:.1f}%)" 
                for val, count in sorted_dist
            }
            
            final_report_unsorted[q_id] = {
                "total_valid_files": total,
                "type": "Static",
                "distribution": dist_dict
            }

        # Processa Dinamiche
        for q_id, data in accumulators.items():
            if data["valid_files"] == 0: continue
            
            total_samples = sum(data["samples"].values())
            sorted_dist = sorted(data["samples"].items(), key=lambda x: x[1], reverse=True)
            
            dist_dict = {
                val: f"{count} ({(count/total_samples)*100:.1f}%)" 
                for val, count in sorted_dist
            }
            
            final_report_unsorted[q_id] = {
                "total_valid_files": data["valid_files"],
                "type": "Dynamic (more answers per file)",
                "total_samples_pool": total_samples,
                "distribution": dist_dict
            }

        # --- 4. ORDINAMENTO PERSONALIZZATO (S prima, poi N) ---
        # Vogliamo l'ordine: S01, S02... S13, N01, N02... N09
        
        def custom_sort_key(key):
            # Restituisce una tupla (Priorità Gruppo, ID Numerico)
            # Priorità 0 per 'S', Priorità 1 per 'N'
            prefix = key[0]
            try:
                number = int(key[1:])
            except ValueError:
                number = 999 # Fallback per chiavi strane
            
            priority = 0 if prefix == 'S' else 1
            return (priority, number)

        sorted_keys = sorted(final_report_unsorted.keys(), key=custom_sort_key)
        
        final_report_ordered = {k: final_report_unsorted[k] for k in sorted_keys}

        # --- 5. SALVATAGGIO ---
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(final_report_ordered, f, indent=4, ensure_ascii=False)
            print(f"Report salvato in: {output_path}\n")
        except Exception as e:
            print(f"Impossibile salvare il report: {e}\n")