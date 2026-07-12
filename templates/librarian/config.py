import os

HOME = os.path.expanduser("~")

# =============================================================================
# AGENT PROFILES
# =============================================================================
# Define each Hermes agent profile to monitor.
# Each key is the profile identifier, value contains:
#   - agent_name: The display name of the agent (matches SOUL.md identity)
#   - db_path: Path to the Hermes state.db for this agent
#
# "default" profile maps to the main agent using ~/.hermes/state.db
# Additional profiles map to ~/.hermes/profiles/<profile-dir>/state.db
#
# Example:
# PROFILES = {
#     "default": {
#         "agent_name": "Ayda",
#         "db_path": f"{HOME}/.hermes/state.db",
#     },
#     "personal-growth-mentor": {
#         "agent_name": "Maya",
#         "db_path": f"{HOME}/.hermes/profiles/personal-growth-mentor/state.db",
#     },
# }

PROFILES = {
    "default": {
        "agent_name": "YourAgentName",          # ← CHANGE THIS
        "db_path": f"{HOME}/.hermes/state.db",
    },
    # Add additional profiles below:
    # "profile-directory-name": {
    #     "agent_name": "AgentDisplayName",
    #     "db_path": f"{HOME}/.hermes/profiles/profile-directory-name/state.db",
    # },
}

# =============================================================================
# PATHS
# =============================================================================
TIMELINE_PATH = f"{HOME}/brain/timeline.json"
LIBRARIAN_DB  = f"{HOME}/librarian/librarian.db"
REPORTS_DIR   = f"{HOME}/brain/reports/daily"
BRAIN_DIR       = f"{HOME}/brain"
VALIDATE_SCRIPT = f"{HOME}/brain/scripts/validate.py"

# =============================================================================
# LLM SETTINGS (Ollama or OpenAI-compatible API)
# =============================================================================
# Ollama (local) — default. Change model to any model you've pulled.
OLLAMA_URL     = "http://localhost:11434/api/chat"
OLLAMA_MODEL   = "qwen2.5:4b"          # ← CHANGE to your preferred model
OLLAMA_TIMEOUT = 600                    # seconds

# For OpenRouter or other OpenAI-compatible APIs, override OLLAMA_URL:
# OLLAMA_URL = "https://openrouter.ai/api/v1/chat/completions"
# OLLAMA_MODEL = "qwen/qwen-2.5-7b-instruct"
# Set your API key in .env: OPENROUTER_API_KEY=sk-...

# =============================================================================
# BEHAVIOR TUNING
# =============================================================================
POLL_INTERVAL        = 10   # Seconds between DB polling cycles
MSG_THRESHOLD        = 20   # Queue a batch when session reaches N new messages
UNGRACEFUL_THRESHOLD = 30   # Minutes of inactivity before treating session as closed
MAX_RETRIES          = 3    # Max retries before moving item to Dead Letter Queue
CRON_HOUR            = 6    # Hour (24h) to generate the daily report
