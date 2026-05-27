import os
import warnings
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY", "")
DEEPEVAL_API_KEY = os.getenv("DEEPEVAL_API_KEY", "")

# LangSmith
LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT", "smart-city-commute-planner")

# MLflow
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
MLFLOW_EXPERIMENT_NAME = os.getenv("MLFLOW_EXPERIMENT_NAME", "commute-planner")

# ChromaDB
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", str(BASE_DIR / "chroma_db"))

# Model settings
LLM_MODEL = "llama-3.3-70b-versatile"
LLM_TEMPERATURE = 0.1
LLM_MAX_TOKENS = 2048

# Prompt compression
COMPRESSION_RATIO = float(os.getenv("COMPRESSION_RATIO", "0.5"))  # 0 = no compression, 1 = max

# SSL — set SSL_VERIFY=false in .env when behind a corporate SSL-inspection proxy
SSL_VERIFY = os.getenv("SSL_VERIFY", "true").lower() != "false"

# Propagate OpenAI key to environment for LangChain
if GROQ_API_KEY:
    os.environ["GROQ_API_KEY"] = GROQ_API_KEY

def build_llm():
    """Central LLM factory — respects SSL_VERIFY for corporate proxy environments."""
    import httpx
    from langchain_groq import ChatGroq
    kwargs: dict = dict(model=LLM_MODEL, temperature=LLM_TEMPERATURE, max_tokens=LLM_MAX_TOKENS)
    if not SSL_VERIFY:
        warnings.filterwarnings("ignore", message="Unverified HTTPS request")
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        kwargs["http_client"] = httpx.Client(verify=False)
    return ChatGroq(**kwargs)


# App
APP_ENV = os.getenv("APP_ENV", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Set LangSmith env vars
if LANGCHAIN_TRACING_V2 and LANGCHAIN_API_KEY:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = LANGCHAIN_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = LANGCHAIN_PROJECT
