import json
from collections import Counter

class DistributionAnalyzer:
    """
    Analizza la distribuzione delle risposte corrette (Ground Truth)
    generate dagli Analyzer e salva un report dettagliato con percentuali.
    """
    
    def __init__(self, spacing_analyzer, naming_analyzer):
        self.analyzers = [spacing_analyzer, naming_analyzer]

    def analyze(self, output_path: str = None):
        """
        Esegue l'analisi e, se specificato, salva un JSON formattato con conteggi e percentuali.
        """
        print(f"\n{'='*60}")
        print("ANALISI DISTRIBUZIONE RISPOSTE (GROUND TRUTH)")
        print(f"{'='*60}")

        # Dizionario contenitore per tutti i risultati
        all_stats = {}

        for analyzer in self.analyzers:
            # Itera su tutti i metodi della classe analyzer
            for method_name in dir(analyzer):
                
                # Cerca solo i metodi che iniziano con "question_"
                if not method_name.startswith("question_"):
                    continue
                
                # Estrai l'ID della domanda (es. "S01")
                q_id = method_name.replace("question_", "")
                
                # Ottieni il riferimento al metodo
                method = getattr(analyzer, method_name)
                
                try:
                    # Esegui la funzione per ottenere i dati (10 campioni)
                    print(f"Analisi in corso: {q_id}...", end="\r") # Stampa e sovrascrive la riga
                    results = method()
                    print(f"Analisi completata: {q_id}   ")
                    
                    if not results:
                        all_stats[q_id] = {"status": "NESSUN RISULTATO"}
                        continue

                    # Estrai solo le risposte corrette (indice 1 della tupla)
                    answers = []
                    for item in results:
                        if isinstance(item, tuple) and len(item) >= 2:
                            # Convertiamo in stringa per usare come chiave nel JSON
                            answers.append(str(item[1]))
                        else:
                            print(f"[WARN] {q_id}: Formato dati imprevisto: {item}")

                    # --- CALCOLO STATISTICHE ---
                    total = len(answers)
                    counts = Counter(answers)
                    
                    # Creiamo il dizionario formattato richiesto: "Valore": "Count, Perc%"
                    formatted_distribution = {}
                    for answer_key, count in counts.items():
                        percentage = (count / total) * 100 if total > 0 else 0
                        # Formato stringa: "N, P%" (es: "576, 48.0%")
                        formatted_distribution[answer_key] = f"{count}, {percentage:.1f}%"

                    # Struttura finale per questa domanda
                    all_stats[q_id] = {
                        "total_samples": total,
                        "distribution": formatted_distribution
                    }

                except Exception as e:
                    print(f"[ERR] Errore analizzando {q_id}: {e}")
                    all_stats[q_id] = {"error": str(e)}

        # --- SALVATAGGIO JSON ---
        if output_path:
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(all_stats, f, indent=4, ensure_ascii=False)
                print(f"✅ Report JSON salvato in: {output_path}")
            except Exception as e:
                print(f"❌ Impossibile salvare il JSON: {e}")