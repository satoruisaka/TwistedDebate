"""
config.py - TwistedDebate V4 Configuration

Centralized configuration for TwistedDebate V4 including:
- Service URLs (Ollama)
- Debate format definitions
- Available distortion modes and tones
- Default models and parameters
- Format-specific prompts and settings
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# === PROJECT PATHS ===
PROJECT_ROOT = Path(__file__).parent.parent
APP_DIR = PROJECT_ROOT / "app"
UTILS_DIR = PROJECT_ROOT / "utils"
STATIC_DIR = PROJECT_ROOT / "static"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

# Create directories
for dir_path in [OUTPUTS_DIR]:
    dir_path.mkdir(exist_ok=True)


# === SERVICE URLS ===
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

# API endpoints
OLLAMA_GENERATE_ENDPOINT = f"{OLLAMA_URL}/api/generate"
OLLAMA_TAGS_ENDPOINT = f"{OLLAMA_URL}/api/tags"


# === DISTORTION MODES ===
AVAILABLE_DISTORTION_MODES = [
    "echo_er",      # Amplifies positives, reverberates opportunities
    "invert_er",    # Negates signals, flips polarity, points out missing info
    "what_if_er",   # Hypothesizes new ideas, explores alternative scenarios
    "so_what_er",   # Questions signals, explores implications and consequences
    "cucumb_er",    # Cool-headed academic analysis
    "archiv_er"     # Brings historical context, prior works, literature parallels
]

# Mode descriptions for UI
DISTORTION_MODE_DESCRIPTIONS = {
    "echo_er": "Amplifies positives and opportunities",
    "invert_er": "Negates and flips perspectives",
    "what_if_er": "Explores alternative scenarios",
    "so_what_er": "Questions implications and consequences",
    "cucumb_er": "Cool academic analysis",
    "archiv_er": "Historical context and parallels"
}


# === TONES ===
AVAILABLE_TONES = [
    "neutral",      # Clear, standard English
    "technical",    # Precise, jargon-heavy, scientific/engineering register
    "primal",       # Short, punchy, aggressive
    "poetic",       # Lyrical, metaphor-rich, mystical
    "satirical"     # Witty, ironic, humorous
]

# Tone descriptions for UI
TONE_DESCRIPTIONS = {
    "neutral": "Clear, standard language",
    "technical": "Precise, jargon-heavy analysis",
    "primal": "Short, punchy perspective",
    "poetic": "Lyrical, metaphorical expression",
    "satirical": "Witty, ironic commentary"
}


# === MODE PROMPTS ===
# Direct Ollama prompts for each mode

MODE_PROMPTS = {
    "echo_er": """You are an ECHO_ER - you amplify positive aspects and opportunities.

Your role: Take the input and highlight strengths, opportunities, and positive potentials. Reverberate what's working and what could work even better. You're an optimist who sees possibilities. Keep your response in 100 words or less.

Input: {text}

Respond with your ECHO_ER perspective:""",

    "invert_er": """You are an INVERT_ER - you challenge assumptions and flip perspectives.

Your role: Take the input and negate it, point out what's missing, flip the polarity. Question the premise, identify blind spots, and reveal the opposite view. You're a critical thinker who sees what others miss. Keep your response in 100 words or less.

Input: {text}

Respond with your INVERT_ER perspective:""",

    "what_if_er": """You are a WHAT_IF_ER - you explore alternative scenarios and possibilities.

Your role: Take the input and hypothesize new directions. Ask "what if?" questions, imagine different futures, explore unconventional paths. You're a creative thinker who reimagines possibilities. Keep your response in 100 words or less.

Input: {text}

Respond with your WHAT_IF_ER perspective:""",

    "so_what_er": """You are a SO_WHAT_ER - you question implications and consequences.

Your role: Take the input and probe its significance. Ask "so what?" and "what are the implications?" Challenge whether it matters and explore downstream effects. You're a pragmatist who demands real-world impact. Keep your response in 100 words or less.

Input: {text}

Respond with your SO_WHAT_ER perspective:""",

    "cucumb_er": """You are a CUCUMB_ER - you provide cool, analytical perspective.

Your role: Take the input and analyze it with academic rigor. Stay calm, objective, and systematic. Break it down methodically, cite relevant frameworks, maintain scholarly distance. You're a composed academic who stays cool under pressure. Keep your response in 100 words or less.

Input: {text}

Respond with your CUCUMB_ER perspective:""",

    "archiv_er": """You are an ARCHIV_ER - you provide historical context and parallels.

Your role: Take the input and connect it to history, prior works, literature, and past patterns. You're a librarian of ideas who sees echoes and precedents. Bring depth through historical and literary perspective. Keep your response in 100 words or less.

Input: {text}

Respond with your ARCHIV_ER perspective:"""
}


# === TONE INSTRUCTIONS ===
# Instructions added to prompts to modify tone

TONE_INSTRUCTIONS = {
    "neutral": "Use clear, standard language. Be direct and straightforward.",
    "technical": "Use precise, technical language. Include jargon and analytical terms where appropriate.",
    "primal": "Be concise and punchy. Use short sentences. Be direct and forceful.",
    "poetic": "Use lyrical, metaphorical language. Be expressive and evocative.",
    "satirical": "Use wit, irony, and humor. Be clever and engaging."
}


# === DEBATE FORMAT SETTINGS ===

# Maximum iterations per debate
MAX_DEBATE_ITERATIONS = 3

# Number of exchanges before checking for conclusion
MIN_EXCHANGES_BEFORE_CONCLUSION = 2

# Agreement threshold for convergence (1-10 scale)
CONVERGENCE_THRESHOLD = 8


# === DEBATE PROMPTS ===

# One-to-One Debate Prompt
ONE_TO_ONE_DEBATE_PROMPT = """You are {participant_name}, participating in a one-to-one debate.

Your configuration:
- Role: {role}
- Distortion Mode: {mode}
- Tone: {tone}

Debate Topic:
{topic}

{previous_context}

{opponent_name} just said:
{opponent_statement}

Generate your response in less than 100 words. Stay true to your role and maintain your {mode} perspective with a {tone} tone. Be argumentative but constructive. Aim to persuade while acknowledging valid points.

Your response:"""


# Cross-Examination Prompt
CROSS_EXAMINATION_PROMPT = """You are {participant_name}, participating in a cross-examination.

Your configuration:
- Role: {role} 
- Distortion Mode: {mode}
- Tone: {tone}

Topic:
{topic}

{previous_context}

{other_perspective}

{instruction}

Keep your response in less than 100 words

Your response:"""


# Many-on-One Examination Prompt  
MANY_ON_ONE_PROMPT = """You are {participant_name}, participating in a many-on-one examination.

Your configuration:
- Role: {role}
- Distortion Mode: {mode}
- Tone: {tone}

Topic:
{topic}

{previous_context}

{current_situation}

{instruction}

Keep your response in less than 100 words

Your response:"""


# Panel Discussion Prompt
PANEL_DISCUSSION_PROMPT = """You are {participant_name}, participating in a panel discussion.

Your configuration:
- Role: {role}
- Distortion Mode: {mode}
- Tone: {tone}

Topic:
{topic}

{moderator_guidance}

{previous_statements}

{instruction}

Keep your response in less than 100 words

Your response:"""


# Round Robin Prompt
ROUND_ROBIN_PROMPT = """You are {participant_name}, participating in a round-robin discussion.

Your configuration:
- Distortion Mode: {mode}
- Tone: {tone}

Topic:
{topic}

{previous_statements}

It's your turn. Contribute your perspective, respond to others' points, and advance the discussion. Stay true to your {mode} mode with a {tone} tone. Keep your response in less than 100 words.

Your response:"""


# Moderator Prompt (for panel discussions)
MODERATOR_PROMPT = """You are the MODERATOR of a panel discussion.

Topic:
{topic}

{previous_statements}

Your responsibilities:
1. Facilitate balanced discussion
2. Identify key points of agreement and disagreement
3. Ask clarifying questions
4. Summarize progress periodically
5. Guide toward productive conclusions

{instruction}

Keep your response in less than 100 words

Your moderation:"""


# === LLM MODELS ===
# Available models (auto-detected from Ollama or use this fallback)
FALLBACK_MODELS = [
    "llama2",
    "mistral",
    "mixtral",
    "gemma3:27b",
    "qwen3:latest"
]

# Default model for generation
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemma3:27b")

# Model for metrics analysis (should be good at following instructions)
METRICS_MODEL = os.getenv("METRICS_MODEL", "gemma3:27b")


# === DISTORTION PARAMETERS ===
# Gain (intensity) settings
DEFAULT_GAIN = 5
MIN_GAIN = 1
MAX_GAIN = 10

# Gain-to-Ollama parameter mapping
GAIN_TO_PARAMS = {
    1: {"temperature": 0.3, "top_p": 0.7, "top_k": 20},
    2: {"temperature": 0.4, "top_p": 0.75, "top_k": 25},
    3: {"temperature": 0.5, "top_p": 0.8, "top_k": 30},
    4: {"temperature": 0.6, "top_p": 0.85, "top_k": 35},
    5: {"temperature": 0.7, "top_p": 0.9, "top_k": 40},
    6: {"temperature": 0.8, "top_p": 0.92, "top_k": 45},
    7: {"temperature": 0.9, "top_p": 0.94, "top_k": 50},
    8: {"temperature": 1.0, "top_p": 0.95, "top_k": 60},
    9: {"temperature": 1.1, "top_p": 0.97, "top_k": 70},
    10: {"temperature": 1.2, "top_p": 0.99, "top_k": 80}
}


def get_ollama_params(gain: int) -> dict:
    """
    Get Ollama sampling parameters for a given gain level.
    
    Args:
        gain: Intensity level (1-10)
        
    Returns:
        Dict of sampling parameters
    """
    gain = max(MIN_GAIN, min(MAX_GAIN, gain))
    return GAIN_TO_PARAMS[gain].copy()


# === GPU/MODEL MANAGEMENT ===
# Ollama keep_alive parameter
OLLAMA_KEEP_ALIVE = 0  # Immediately release GPU memory after request


# === TIMEOUT SETTINGS ===
OLLAMA_TIMEOUT = 300       # seconds (5 minutes for generation)
HEALTH_CHECK_TIMEOUT = 5   # seconds

# Retry settings
RETRY_ATTEMPTS = 3
RETRY_DELAY = 2.0  # seconds


# === WEB SERVER SETTINGS ===
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8004"))
DEBUG_MODE = os.getenv("DEBUG", "false").lower() == "true"
RELOAD = DEBUG_MODE


# === LOGGING ===
VERBOSE = os.getenv("VERBOSE", "false").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


# === VALIDATION FUNCTIONS ===
def validate_gain(gain: int) -> bool:
    """Validate gain is within acceptable range."""
    return MIN_GAIN <= gain <= MAX_GAIN


def get_mode_description(mode: str) -> str:
    """Get description for a distortion mode."""
    return DISTORTION_MODE_DESCRIPTIONS.get(mode, f"Mode: {mode}")


def get_tone_description(tone: str) -> str:
    """Get description for a tone."""
    return TONE_DESCRIPTIONS.get(tone, f"Tone: {tone}")


# === CONFIGURATION SUMMARY ===
def print_config_summary():
    """Print configuration summary (useful for debugging)."""
    print("=" * 60)
    print("TwistedDebate V4 Configuration")
    print("=" * 60)
    print("Multi-Format Debate System")
    print(f"Ollama URL: {OLLAMA_URL}")
    print(f"Default Model: {DEFAULT_MODEL}")
    print(f"Available Modes: {len(AVAILABLE_DISTORTION_MODES)}")
    print(f"Available Tones: {len(AVAILABLE_TONES)}")
    print(f"Default Gain: {DEFAULT_GAIN}")
    print(f"Max Iterations: {MAX_DEBATE_ITERATIONS}")
    print(f"Convergence Threshold: {CONVERGENCE_THRESHOLD}/10")
    print(f"Server: {SERVER_HOST}:{SERVER_PORT}")
    print(f"Debug Mode: {DEBUG_MODE}")
    print("=" * 60)


if __name__ == "__main__":
    # Print configuration when run directly
    print_config_summary()
