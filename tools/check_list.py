import re
import os
import anthropic  # Import the Anthropic SDK
import time
from typing import Dict, List, Any

# API_KEY = os.environ.get("ANTHROPIC_API_KEY")
API_KEY = "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"

class ClaudeBatchAnalyzer:
    """
    Analyzes a full interview transcript (Batch) and
    returns a list of all themes that were discussed.
    """
    def __init__(self, themes: Dict[str, str], api_key: str):
        if not api_key:
            raise ValueError(
                "Anthropic API key not found. "
                "Please set it in the script or via "
                "the ANTHROPIC_API_KEY environment variable."
            )
        self.themes = themes
        self.client = anthropic.Anthropic(api_key=api_key)

    def _build_prompt(self, full_transcript: str) -> str:
        """
        Builds the prompt for the "post-interview" batch analysis.
        """
        prompt = "You are an expert assistant in 'Quant' interview analysis.\n\n"
        prompt += "Here is the list of all the themes we are tracking. Read their descriptions carefully:\n"
        prompt += "<themes_to_track>\n"
        for tag, description in self.themes.items():
            prompt += f"{tag}: {description}\n"
        prompt += "</themes_to_track>\n\n"
        
        prompt += "Here is the full transcript of an interview:\n"
        prompt += "<full_transcript>\n"
        prompt += full_transcript
        prompt += "\n</full_transcript>\n\n"
        prompt += "TASK: Analyze the transcript. Identify ALL themes that were substantially discussed, either by the recruiter or the candidate.\n\n"
        prompt += "RESPONSE FORMAT: Respond *only* with a Python-style list of the tags for the themes that were covered. Do not add any other text.\n"
        prompt += f"Example of the response format: ['{list(self.themes.keys())[0]}', '{list(self.themes.keys())[1]}', '{list(self.themes.keys())[-1]}']"
        
        return prompt

    def _parse_response(self, response_text: str) -> List[str]:
        """
        Extracts the list of tags from Claude's raw response.
        
        This uses re.findall to find all [TAG] instances, which is
        robust even if the LLM returns a malformed list.
        """
        tags = re.findall(r"\[([0-9A-Z_]+)\]", response_text)
        return [f"[{tag}]" for tag in tags]

    def analyze_text(self, transcript: str, verbose: bool=False) -> List[str]:
        """
        Runs the complete analysis of the transcript.
        """
        if verbose:
            print("[INFO] Starting 'Batch Analysis' (Single Prediction)...")
        prompt = self._build_prompt(transcript)
        
        start_time = time.time()
        if verbose:
            print("  [INFO] Calling Claude API (Sonnet)...")
        
        try:
            message = self.client.messages.create(
                # For long transcript analysis, Sonnet is a good balance.
                model="claude-3-haiku-20240307", 
                max_tokens=1000, # Leave room for the list
                system="You are an interview analyzer. Respond *only* in the requested list format.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            raw_response = message.content[0].text
        
        except anthropic.AuthenticationError:
            print("  [ERROR] Authentication failed. Is your API key correct?")
            return []
        except Exception as e:
            print(f"  [ERROR] API call error: {e}")
            return []
            
        end_time = time.time()
        latency = end_time - start_time
        
        if verbose:
            print(f"  [INFO] Claude API call completed in {latency:.2f} seconds.")
            print(f"  [DEBUG] Raw response from Claude:\n{response_text}")
        # --- Parse the response ---
        covered_themes = self._parse_response(raw_response)
        return covered_themes

# --- HELPER FUNCTION (unchanged logic) ---
def format_conversation(dialogue: List[Dict[str, str]]) -> str:
    """Transforms the list of dicts into a single readable string."""
    transcript = ""
    for turn in dialogue:
        transcript += f"{turn['speaker']}: {turn['text']}\n"
    return transcript

# --- CONFIGURATION (Challenging Test Set) ---

# 1. Themes (English descriptions)
challenging_themes = {
    "[CV_TECHNIQUES]": "Cross-validation, K-Fold, Walk-Forward, backtesting, out-of-sample robustness.",
    "[REGULARIZATION]": "L1/L2 regularization, Lasso, Ridge, preventing overfitting via coefficient penalty.",
    "[FEATURE_SELECTION]": "Variable selection, feature engineering, SHAP, LIME, PCA, feature importance.",
    "[STATIONARITY]": "Stationarity, non-stationarity, unit root tests (ADF, KPSS), co-integration.",
    "[TIME_SERIES_MODELS]": "Specific time series models (ARIMA, GARCH, VAR), volatility modeling.",
    "[OPTIMIZATION_PYTHON]": "Python code performance, vectorization, NumPy, Pandas, Numba, Cython.",
    "[LOOKAHEAD_BIAS]": "Look-ahead bias, future data leakage, common backtesting errors.",
    "[DATA_PIPELINE]": "Data cleaning, ingestion, ETL pipelines, market data management.",
    "[BEHAVIORAL_PRESSURE]": "Handling stress, tight deadlines, crisis situations.",
    "[BEHAVIORAL_TEAMWORK]": "Collaboration, conflict management, communication with PMs or traders.",
    "[EXTRA]": "Off-topic questions, greetings, transitions, questions about the job."
}
suggested_questions = {
    "[SUGGESTED_1]":"How do you ensure a model is not overfitting?",
    "[SUGGESTED_2]":"Explain the concept of stationarity and its importance.",
    "[SUGGESTED_3]":"Was the code fast?"
} 

all_themes = {**challenging_themes, **suggested_questions}
occurrences = {tag: 0 for tag in all_themes.keys()}


# 2. Conversation (Using the French conversation as test data)
challenging_conversation_flow = [
    {"speaker": "Recruiter", "text": "Thanks for coming in. To start, could you walk me through your most recent research project?"},
    {"speaker": "Candidate", "text": "Certainly. I developed a mid-frequency statistical arbitrage strategy. The core was identifying mean-reverting pairs, but the real challenge was in the data pipeline, specifically handling asynchronous market data and ensuring timestamps were clean before feeding them into the model."},
    {"speaker": "Recruiter", "text": "That's interesting. You mentioned cleaning the data. What's the worst data integrity issue you've personally encountered?"},
    {"speaker": "Candidate", "text": "On a previous project, we had a subtle look-ahead bias. The backtest was using dividend adjustment data that wasn't available until the *end* of the day, but our model was trading *intra-day*. It took a week to find; the PnL looked amazing until we fixed it."},
    {"speaker": "Recruiter", "text": "A classic, painful problem. So, when you're building a new model, how do you differentiate between true alpha and just factor risk? For instance, how do you know your model isn't just a proxy for 'value' or 'momentum'?"},
    {"speaker": "Candidate", "text": "That's the key question. We run extensive risk decomposition. I use PCA to identify the main drivers, but more importantly, I neutralize the portfolio against known factors—like Fama-French—to isolate the idiosyncratic, or 'true,' alpha. If the signal disappears after neutralization, it wasn't a real signal."},
    {"speaker": "Recruiter", "text": "When you're doing that neutralization, you often end up with a high-dimensional problem. How do you select your final predictors and avoid overfitting at the same time? Are you a fan of Lasso?"},
    {"speaker": "Candidate", "text": "I am. I use Lasso (L1) heavily for that exact reason: it performs feature selection and regularization in one step. If L1 is too aggressive, I'll test Ridge or ElasticNet. But for validation, I rely on walk-forward cross-validation, not just a simple K-Fold, as it's crucial for time-series data."},
    {"speaker": "Recruiter", "text": "Let's change topics. Tell me about a time you had a strong disagreement with a Portfolio Manager about a model."},
    {"speaker": "Candidate", "text": "A PM wanted to push a model live that I felt was unstable. The backtest looked good, but the Sharpe ratio was heavily dependent on a few outlier days. We had a heated debate, but I brought a new analysis—the full NumPy code for a Monte Carlo simulation I'd written overnight—to show the fragility. He wasn't happy, but we didn't push it live."},
    {"speaker": "Recruiter", "text": "You wrote the simulation overnight? Was the code fast?"},
    {"speaker": "Candidate", "text": "It had to be. I didn't use any 'for' loops; it was all vectorized NumPy operations to simulate 10,000 paths. It ran in about 30 seconds."},
    {"speaker": "Recruiter", "text": "Impressive. Final question: why are you looking to leave your current role?"},
    {"speaker": "Candidate", "text": "I'm looking for new challenges, and your team's reputation for rigorous, foundational research is really what attracts me."}
]

verbose = False

if not API_KEY or API_KEY == "votre_cle_api_anthropic_ici":
    print("="*50)
    print("ERREUR : Clé API non configurée.")
    print("Veuillez éditer le script et ajouter votre clé API Claude")
    print("à la variable 'API_KEY' en haut du fichier.")
    print("="*50)
else:
    if verbose:
        print("Initialisation du Moteur Zero-Shot Claude (API)...")
    engine = ClaudeBatchAnalyzer(themes=all_themes, api_key=API_KEY)
    if verbose:
        print("Moteur prêt.\n")
        print("--- DÉBUT DE LA SIMULATION D'ENTRETIEN ---")
    output = []
    speaker = challenging_conversation_flow[0]["speaker"]
    current_text = f"[{speaker}]"
    for sentence in challenging_conversation_flow:
        if speaker == "Recruiter" and sentence["speaker"] == "Candidate":
            current_text += f"[Candidate] {sentence["text"]}"
            speaker = "Candidate"
        elif speaker == "Candidate" and sentence["speaker"] == "Recruiter":
            covered_themes = engine.analyze_text(current_text)
            output.append({'text': current_text, 'covered_theme': covered_themes})
            for theme in covered_themes:
                if theme in list(all_themes.keys()):
                    occurrences[theme] += 1
            current_text = f"[Recruiter] {sentence["text"]}"
            speaker = "Recruiter"
        else:
            current_text += f" {sentence["text"]}"
    covered_themes = engine.analyze_text(current_text)
    output.append({'text': current_text, 'covered_theme': covered_themes})
    for theme in covered_themes:
        if theme in list(all_themes.keys()):
            occurrences[theme] += 1
    
    
    print("\n--- RÉSULTATS DE L'ANALYSE DE L'ENTRETIEN ---")
    # Présentation synthétique et lisible des résultats d'occurrence
    print("\n" + "="*60)
    print("RÉSULTAT : Occurrences des thèmes détectés")
    print("="*60)

    # Nombre de segments analysés
    num_segments = len(output) if 'output' in globals() else 0
    print(f"Segments analysés : {num_segments}\n")

    # Séparer thèmes principaux et suggestions
    suggested_keys = set(suggested_questions.keys())
    main_keys = [k for k in occurrences.keys() if k not in suggested_keys]

    # Thèmes principaux triés par occurrences décroissantes
    sorted_main = sorted(main_keys, key=lambda k: occurrences.get(k, 0), reverse=True)

    print("Thèmes (triés par fréquence) :")
    for tag in sorted_main:
        count = occurrences.get(tag, 0)
        desc = all_themes.get(tag, "")
        if count > 0:
            print(f"  {tag:25} — {count:3d} occurrences — {desc}")
    # Afficher ceux à zéro en bloc, si nécessaire
    zeros = [t for t in sorted_main if occurrences.get(t, 0) == 0]
    if zeros:
        print("\nThèmes non détectés :")
        for tag in zeros:
            print(f"  {tag}")

    # Suggestions traitées à part
    print("\n" + "-"*60)
    print("Questions suggérées (traitées séparément) :")
    for tag, q in suggested_questions.items():
        count = occurrences.get(tag, 0)
        print(f"  {tag:15} — {count:3d} occurrences — {q}")
    print("\n" + "="*60)
    print("Fin du rapport.")
    print("="*60)