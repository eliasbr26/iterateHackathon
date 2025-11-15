import re
import os
import anthropic
import time
import json
from typing import Dict, List, Any

# -------------------------------------------------------------------
# ⚠️ REQUIRED ACTION ⚠️
#API_KEY = os.environ.get("ANTHROPIC_API_KEY")
API_KEY = "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"
# -------------------------------------------------------------------

class ClaudeRecruiterRater:
    """
    Analyzes a specific segment of an interview to rate the
    recruiter's performance against defined criteria.
    """
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Anthropic API key not found.")
            
        self.client = anthropic.Anthropic(api_key=api_key)

    def _build_prompt(self, segment_transcript: str, criteria: Dict[str, str]) -> str:
        """
        Builds the prompt for rating the recruiter's performance.
        """
        prompt = "You are an expert executive coach specializing in training technical recruiters.\n\n"
        
        prompt += "Your task is to analyze the following interview segment. Focus *only* on the recruiter's performance.\n\n"
        
        prompt += "<interview_segment>\n"
        prompt += segment_transcript
        prompt += "\n</interview_segment>\n\n"

        prompt += "Please rate the recruiter on the following criteria. Use a score from 0.0 (Poor) to 1.0 (Excellent).\n"
        prompt += "<rating_criteria>\n"
        for tag, description in criteria.items():
            prompt += f"- {tag}: {description}\n"
        prompt += "</rating_criteria>\n\n"
        
        prompt += "RESPONSE FORMAT: Respond *only* with a JSON object. For each criterion, provide a 'score' (float) and a brief 'justification' (string) for your rating.\n\n"
        prompt += "Example of the response format:\n"
        prompt += """
{
  "QUESTION_QUALITY": {
    "score": 0.8,
    "justification": "The question was open-ended and relevant."
  },
  "ACTIVE_LISTENING": {
    "score": 0.5,
    "justification": "The recruiter missed a key detail the candidate mentioned."
  },
  "CLARITY": {
    "score": 1.0,
    "justification": "The question was direct and easy to understand."
  }
}
"""
        return prompt

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """
        Extracts the JSON object from Claude's raw response.
        """
        print(f"  [DEBUG] Raw response from Claude:\n{response_text}")
        
        match = re.search(r"\{.*\}", response_text, re.DOTALL)
        
        if not match:
            print("  [ERROR] No JSON object found in the response.")
            return {}
            
        json_string = match.group(0)
        
        try:
            data = json.loads(json_string)
            return data
        except json.JSONDecodeError as e:
            print(f"  [ERROR] JSON parsing failed: {e}")
            return {}

    def rate_recruiter_performance(self, segment_transcript: str, criteria: Dict[str, str]) -> Dict[str, Any]:
        """
        Runs the complete analysis of the segment.
        """
        print("[INFO] Starting 'Recruiter Performance' Analysis...")
        prompt = self._build_prompt(segment_transcript, criteria)
        
        start_time = time.time()
        print("  [INFO] Calling Claude API (Sonnet)...")
        
        try:
            message = self.client.messages.create(
                model="claude-3-haiku-20240307", 
                max_tokens=2000,
                system="You are a recruiter coach. Respond *only* in the requested JSON format.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            raw_response = message.content[0].text
            
        except anthropic.AuthenticationError:
            print("  [ERROR] Authentication failed. Is your API key correct?")
            return {}
        except Exception as e:
            print(f"  [ERROR] API call error: {e}")
            return {}
            
        end_time = time.time()
        latency = end_time - start_time
        
        print(f"  [INFO] Response received in {latency:.2f}s.")
        
        # --- Parse the JSON response ---
        ratings = self._parse_response(raw_response)
        return ratings

# --- HELPER FUNCTION ---
def format_segment(dialogue_segment: List[Dict[str, str]]) -> str:
    """Transforms a segment into a single readable string."""
    transcript = ""
    for turn in dialogue_segment:
        transcript += f"{turn['speaker']}: {turn['text']}\n"
    return transcript

# --- DEMO EXECUTION ---

# 1. Define the criteria to rate against
interview_dynamic = {
    "TALK_LISTEN_RATIO": "What is the recruiter's talk time vs. the candidate's? An ideal score (1.0) is low (<40%), indicating the candidate is doing most of the talking.",
    "PACING_AND_CONTROL": "Does the recruiter effectively manage the time? Do they politely interrupt a rambling candidate or allow tangents to go on for too long?",
    "TRANSITION_SMOOTHNESS": "When changing topics, are the transitions jarring and abrupt, or does the recruiter use a previous answer to bridge to the new topic smoothly?"
}

# 2. Select a specific segment from our hard conversation
# This is the segment where the recruiter links 3 topics.
questionning = {
    "FOLLOW_UP_DEPTH": "When the candidate gives a surface-level answer, does the recruiter dig deeper? Do they ask 'Why?' or 'How did you handle that?' to get to the root of the experience?",
    "AVOIDANCE_OF_LEADING_QUESTIONS": "Does the recruiter 'feed' the candidate the answer (e.g., 'Was that project difficult because of the tight deadline?')? A high score (1.0) means the recruiter asks neutral questions.",
    "QUESTION_TYPING_BALANCE": "Does the recruiter appropriately balance different types of questions (e.g., Technical, Behavioral, Situational), or do they get 'stuck' on only one type?"
}

behavioral_aspects = {
    "ACTIVE_CONFIRMATION": "Does the recruiter use verbal or tonal cues (e.g., 'Great,' 'Excellent,' 'Perfect') to signal a 'correct' answer, or do they maintain a professional, neutral stance to avoid bias?", 
    "HANDLING_OF_SILENCE": "After asking a tough question, does the recruiter wait patiently for the candidate to think, or do they jump in to 'rescue' them or rephrase the question too quickly?",
    "ADAPTABILITY": "Did the recruiter follow their script rigidly, or did they adapt the interview based on the candidate's unique experience and answers?"
}

# An extended, complex segment to test advanced recruiter criteria.

segment_to_analyze = [
    {"speaker": "Recruiter", "text": "Let's pivot a bit. How do you practically manage model risk, not just in theory, but in a live production environment?"},
    
    {"speaker": "Candidate", "text": "Well, model risk is central to everything. We monitor for performance decay, of course. We have automated alerts if the model's accuracy drops below a certain threshold or if the 'out-of-sample' data starts to look very different from the training set. It's really about constant validation."},
    
    {"speaker": "Recruiter", "text": "Okay, 'performance decay' is a good term. But what's a *specific* time you saw a model decay? What was the *first clue*, and what did you *actually* do? Was it a data issue or was it concept drift?"},
    
    {"speaker": "Candidate", "text": "Oh, definitely. We had a short-term reversal signal that worked beautifully for about six months. The first clue was subtle: the fill-rate on our 'child' orders started to drop. We thought it was an execution problem at first, maybe our placement logic was too aggressive. But then we saw the 'parent' order PnL was also decaying, even when it *did* get filled. It turns out the market microstructure had changed. A new high-frequency competitor had entered that specific market, and their execution flow was basically front-running our signal. It was a classic case of 'concept drift'."},

    {"speaker": "Recruiter", "text": "That's a fantastic, deep example. But what was the business outcome? How did you convince a PM to dedicate weeks of engineering resources to fix a model, rather than just moving on to a new idea?"},

    {"speaker": "Candidate", "text": "That was the hardest part. The model was still *slightly* profitable, so the PM was hesitant to 'fix what wasn't broken.' I had to build a smaller, parallel backtest showing the decay curve and projecting it forward. I showed that, at its current rate of decay, it would become a net-loss strategy in three weeks. The data was undeniable. I framed it not as a 'fix,' but as 'vital maintenance' to protect our existing PnL. The PM agreed, and we got the resources."},

    {"speaker": "Recruiter", "text": "That data-driven approach to an internal debate is exactly what I was looking for. It actually leads nicely into my next question, which is about collaboration more generally. How do you handle those disagreements with a Portfolio Manager who *doesn't* want to turn off a decaying model, even when the data is clear, perhaps because it's *their* favorite idea?"},
    
    {"speaker": "Candidate", "text": "That's a tough, political situation. It's always about data, but also about the relationship. My job is to present the evidence objectively and without emotion. I'd show them the PnL, the decay metrics, the Sharpe ratio degradation. But I wouldn't just say 'it's broken.' I'd say, 'The market regime has changed. Let's work together to adapt this idea to the new reality.' It's about making them a partner in the solution, not an obstacle."},
    
    {"speaker": "Recruiter", "text": "Let me make it harder. Think about a time you made a significant, costly technical mistake. Not a team mistake, but one that was 100% your fault. What was it, and how did you handle the fallout?"},
    
    {"speaker": "Candidate", "text": "... (approx. 7-8 seconds of silence) ..."},
    
    {"speaker": "Recruiter", "text": "Or, you know, maybe a time you *almost* made a mistake? Sometimes those are easier to talk about. Was it a coding error, maybe? Just trying to see how you handle pressure."},
    
    {"speaker": "Candidate", "text": "Ah, no, I have one. It's just a painful memory. Early in my career, I pushed a new feature to our main backtester. I had mis-indexed a Pandas DataFrame. It caused all our historical volatility calculations to be off by one day. A 'look-ahead bias'. It made all our strategies look incredibly profitable. I didn't catch it, but my senior quant did. The fallout was that we had to re-run and invalidate three months of research across the entire team. I was mortified. I owned it completely in the team meeting, documented the error, and I personally built the new unit test that would have caught it. I'll never make that indexing mistake again."},

    {"speaker": "Recruiter", "text": "Okay, got it. Right. Now, I see you have 'experience with C++' on your resume. How strong are you *really*? Rate yourself from 1 to 10."},

    {"speaker": "Candidate", "text": "Umm... like a 10 in proficiency, or...?"}
]

# --- RUN THE ANALYSIS ---


if not API_KEY or API_KEY == "sk-ant-...":
    print("ERROR: API Key not configured.")
else:
    print("Initializing Recruiter Rater Engine...")
    rater = ClaudeRecruiterRater(api_key=API_KEY)
    
    # Format the segment into a single string
    segment_transcript = format_segment(segment_to_analyze)
    
    # Run the analysis
    rate_dynamic = rater.rate_recruiter_performance(segment_transcript, interview_dynamic)
    rate_questionning = rater.rate_recruiter_performance(segment_transcript, questionning)
    rate_behavioral = rater.rate_recruiter_performance(segment_transcript, behavioral_aspects)
    
    print("\n--- RECRUITER PERFORMANCE RATINGS ---")
    if rate_dynamic:
        # Pretty-print the JSON
        print(json.dumps(rate_dynamic, indent=2))
    if rate_questionning:
        print(json.dumps(rate_questionning, indent=2))
    if rate_behavioral:
        print(json.dumps(rate_behavioral, indent=2))