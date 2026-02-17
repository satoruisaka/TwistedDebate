"""
models.py - Data models for TwistedDebate V4

Defines request/response models for the FastAPI application supporting
multiple debate formats.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from enum import Enum


# === ENUMS ===

class DebateFormat(str, Enum):
    """Available debate formats."""
    ONE_TO_ONE = "one-to-one"
    CROSS_EXAM = "cross-exam"
    MANY_ON_ONE = "many-on-one"
    PANEL = "panel"
    ROUND_ROBIN = "round-robin"


class DistortionMode(str, Enum):
    """Distortion modes for rhetorical perspectives."""
    ECHO_ER = "echo_er"
    INVERT_ER = "invert_er"
    WHAT_IF_ER = "what_if_er"
    SO_WHAT_ER = "so_what_er"
    CUCUMB_ER = "cucumb_er"
    ARCHIV_ER = "archiv_er"


class DistortionTone(str, Enum):
    """Tone styles for output generation."""
    NEUTRAL = "neutral"
    TECHNICAL = "technical"
    PRIMAL = "primal"
    POETIC = "poetic"
    SATIRICAL = "satirical"


class ConvergenceStatus(str, Enum):
    """Convergence status indicator."""
    CONVERGING = "Converging"
    DIVERGING = "Diverging"
    STABLE = "Stable"
    UNKNOWN = "Unknown"


class SensitivityLevel(str, Enum):
    """Sensitivity/intensity level indicator."""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class BiasLevel(str, Enum):
    """Bias level indicator."""
    LOW = "Low"
    NEUTRAL = "Neutral"
    HIGH = "High"


# === PARTICIPANT MODELS ===

class ParticipantConfig(BaseModel):
    """Configuration for a single participant."""
    role: str = Field(description="Participant role (e.g., 'debater1', 'examiner')")
    label: str = Field(description="Display label for the participant")
    model: str = Field(description="LLM model name or 'USER'")
    mode: DistortionMode = Field(description="Distortion mode")
    tone: DistortionTone = Field(description="Tone variation")


# === MESSAGE MODELS ===

class DebateMessage(BaseModel):
    """A single message in the debate transcript."""
    speaker: str = Field(description="Speaker name/label")
    content: str = Field(description="Message content")
    role: str = Field(description="Speaker role")
    iteration: Optional[int] = Field(default=None, description="Iteration number")
    timestamp: Optional[str] = Field(default=None, description="Message timestamp")


class KeyStatement(BaseModel):
    """A key statement summary."""
    speaker: str = Field(description="Speaker name")
    text: str = Field(description="Summary of key point")
    iteration: Optional[int] = Field(default=None, description="Iteration number")


# === METRICS MODELS ===

class DebateMetrics(BaseModel):
    """Metrics tracking debate progress."""
    iteration: int = Field(description="Current iteration number")
    status: str = Field(description="Debate status")
    agreementScore: Optional[float] = Field(default=None, description="Agreement score (0-10)")
    convergenceStatus: Optional[ConvergenceStatus] = Field(default=None)
    emotionalSensitivity: Optional[SensitivityLevel] = Field(default=None)
    biasLevel: Optional[BiasLevel] = Field(default=None)
    topicDrift: Optional[SensitivityLevel] = Field(default=None)


# === RECORD FILE MODELS ===

class RecordFile(BaseModel):
    """Information about the saved debate record."""
    filename: str = Field(description="Record filename")
    path: str = Field(description="Full file path")
    url: str = Field(description="URL to access the record")


# === REQUEST MODELS ===

class DebateV4Request(BaseModel):
    """Request model for V4 debate."""
    topic: str = Field(..., description="Debate topic/question", min_length=1)
    format: DebateFormat = Field(..., description="Debate format")
    participants: List[ParticipantConfig] = Field(..., description="List of participants")
    
    maxIterations: Optional[int] = Field(default=10, ge=1, le=50, description="Maximum iterations")
    gain: Optional[int] = Field(default=5, ge=1, le=10, description="Debate intensity")


class UserInputRequest(BaseModel):
    """Request for submitting user input during debate."""
    debateId: str = Field(..., description="Debate session ID")
    userId: str = Field(..., description="User participant ID")
    content: str = Field(..., description="User's input text")


class GenerateTurnRequest(BaseModel):
    """Request for generating a single participant turn."""
    topic: str = Field(..., description="Debate topic", min_length=1)
    participant: ParticipantConfig = Field(..., description="Participant to generate for")
    previousMessages: List[DebateMessage] = Field(default=[], description="Previous debate messages")
    iteration: int = Field(..., ge=1, description="Current iteration number")
    maxIterations: Optional[int] = Field(default=10, ge=1, description="Total iterations in debate")
    gain: Optional[int] = Field(default=5, ge=1, le=10, description="Debate intensity")
    format: Optional[DebateFormat] = Field(default=None, description="Debate format context")


class AnalyzeDebateRequest(BaseModel):
    """Request for analyzing debate and generating metrics."""
    topic: str = Field(..., description="Debate topic")
    messages: List[DebateMessage] = Field(..., description="Debate messages to analyze")
    iteration: int = Field(..., description="Current iteration number")


# === RESPONSE MODELS ===

class ConfigResponse(BaseModel):
    """Response model for /api/config endpoint."""
    modes: List[str] = Field(description="Available distortion modes")
    tones: List[str] = Field(description="Available tone variations")
    modeDescriptions: Dict[str, str] = Field(description="Mode descriptions")
    toneDescriptions: Dict[str, str] = Field(description="Tone descriptions")


class ModelsResponse(BaseModel):
    """Response model for /api/models endpoint."""
    models: List[str] = Field(description="Available Ollama models")


class GenerateTurnResponse(BaseModel):
    """Response model for single turn generation."""
    message: DebateMessage = Field(description="Generated message")
    success: bool = Field(description="Whether generation succeeded")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class AnalyzeDebateResponse(BaseModel):
    """Response model for debate analysis."""
    metrics: DebateMetrics = Field(description="Calculated debate metrics")
    success: bool = Field(description="Whether analysis succeeded")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class DebateV4Response(BaseModel):
    """Response model for V4 debate."""
    topic: str = Field(description="Debate topic")
    format: DebateFormat = Field(description="Debate format used")
    participants: List[ParticipantConfig] = Field(description="Participant configurations")
    
    messages: List[DebateMessage] = Field(description="Debate transcript")
    metrics: DebateMetrics = Field(description="Current debate metrics")
    
    keyStatements: Optional[List[KeyStatement]] = Field(default=None)
    recordFile: Optional[RecordFile] = Field(default=None)
    
    completed: bool = Field(description="Whether debate is completed")
    convergenceReached: Optional[bool] = Field(default=None)
    
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(description="Overall health status")
    ollama_available: bool = Field(description="Ollama service availability")
    timestamp: str = Field(description="Check timestamp")


# === STREAMING MODELS (for future WebSocket support) ===

class DebateStreamEvent(BaseModel):
    """A streaming debate event."""
    type: Literal["message", "metrics", "status", "error", "complete"] = Field(
        description="Event type"
    )
    data: Dict[str, Any] = Field(description="Event data")
    timestamp: str = Field(description="Event timestamp")


# === INTERNAL MODELS ===

class DebateState(BaseModel):
    """Internal state for an active debate (not exposed via API)."""
    debateId: str
    topic: str
    format: DebateFormat
    participants: List[ParticipantConfig]
    messages: List[DebateMessage]
    metrics: DebateMetrics
    keyStatements: List[KeyStatement]
    
    currentIteration: int = 0
    completed: bool = False
    convergenceReached: bool = False
    
    # For tracking participants who haven't responded
    pendingParticipants: List[str] = []
    
    # User participation tracking
    userParticipantRole: Optional[str] = None
    awaitingUserInput: bool = False


class DebateAnalysis(BaseModel):
    """Analysis result from moderator or analyzer."""
    agreementScore: float = Field(ge=0, le=10)
    convergenceStatus: ConvergenceStatus
    emotionalSensitivity: SensitivityLevel
    biasLevel: BiasLevel
    topicDrift: SensitivityLevel
    summary: str
    keyPoints: List[str]
    shouldContinue: bool


# === UTILITY MODELS ===

class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(description="Error message")
    detail: Optional[str] = Field(default=None, description="Detailed error information")
    timestamp: str = Field(description="Error timestamp")
