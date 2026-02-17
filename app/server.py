"""
server.py - FastAPI server for TwistedDebate V4

Provides web interface for multi-format debate system.
"""

import os
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.models import (
    DebateV4Request,
    DebateV4Response,
    GenerateTurnRequest,
    GenerateTurnResponse,
    AnalyzeDebateRequest,
    AnalyzeDebateResponse,
    ConfigResponse,
    ModelsResponse,
    HealthResponse,
    DebateMessage,
    DebateMetrics,
    KeyStatement,
    RecordFile
)
from app.facilitator import Facilitator
from app import config

# Initialize FastAPI app
app = FastAPI(
    title="TwistedDebate V4",
    description="Multi-format debate system using Ollama",
    version="4.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
static_dir = Path(__file__).parent.parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Mount outputs directory for debate records
outputs_dir = Path(__file__).parent.parent / "outputs"
outputs_dir.mkdir(exist_ok=True)
app.mount("/outputs", StaticFiles(directory=outputs_dir), name="outputs")

# Initialize Facilitator
facilitator = Facilitator(verbose=config.VERBOSE)


@app.get("/")
async def root():
    """Serve V4 debate web interface."""
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    else:
        raise HTTPException(status_code=404, detail="index.html not found")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check system health."""
    health_status = facilitator.check_health()
    
    return HealthResponse(
        status="healthy" if health_status["ollama_available"] else "degraded",
        ollama_available=health_status["ollama_available"],
        timestamp=datetime.utcnow().isoformat()
    )


@app.get("/api/models", response_model=ModelsResponse)
async def list_models():
    """List available Ollama models for selection."""
    try:
        models = facilitator.list_ollama_models()
        return ModelsResponse(models=models)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching models: {str(e)}"
        )


@app.get("/api/config", response_model=ConfigResponse)
async def get_config():
    """Get configuration including available modes and tones."""
    try:
        return ConfigResponse(
            modes=[mode for mode in config.AVAILABLE_DISTORTION_MODES],
            tones=[tone for tone in config.AVAILABLE_TONES],
            modeDescriptions=config.DISTORTION_MODE_DESCRIPTIONS,
            toneDescriptions=config.TONE_DESCRIPTIONS
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching config: {str(e)}"
        )


@app.post("/api/debate-v4", response_model=DebateV4Response)
async def generate_debate_v4(request: DebateV4Request):
    """
    Generate V4 debate based on selected format.
    
    Supports:
    - One-to-One Debate
    - Cross-Examination
    - Many-on-One Examination
    - Panel Discussion
    - Round Robin
    """
    print(f"\n[V4 Endpoint] Received {request.format.value} debate request")
    print(f"[V4 Endpoint] Topic: {request.topic[:50]}...")
    print(f"[V4 Endpoint] Participants: {len(request.participants)}")
    print(f"[V4 Endpoint] Max iterations: {request.maxIterations}, Gain: {request.gain}")
    
    try:
        # Run the debate
        print("[V4 Endpoint] Calling facilitator.run_debate()...")
        result = facilitator.run_debate(
            topic=request.topic,
            format=request.format,
            participants=request.participants,
            max_iterations=request.maxIterations,
            gain=request.gain
        )
        print("[V4 Endpoint] Debate completed successfully")
        
        # Convert result to response model
        response = DebateV4Response(
            topic=result["topic"],
            format=result["format"],
            participants=result["participants"],
            messages=result["messages"],
            metrics=result["metrics"],
            keyStatements=result.get("keyStatements", []),
            recordFile=result.get("recordFile"),
            completed=result["completed"],
            convergenceReached=result.get("convergenceReached"),
            metadata={
                "timestamp": datetime.utcnow().isoformat(),
                "maxIterations": request.maxIterations,
                "gain": request.gain
            }
        )
        
        # Save results (optional - implement later)
        # try:
        #     saved_path = save_debate_record(response)
        #     print(f"[TwistedDebate V4] Results saved to: {saved_path}")
        # except Exception as e:
        #     print(f"[TwistedDebate V4] Warning: Failed to save record: {e}")
        
        return response
        
    except ValueError as e:
        # Validation errors
        print(f"\n[V4 Endpoint ERROR] Validation error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid request: {str(e)}"
        )
    except Exception as e:
        # Other errors
        import traceback
        error_trace = traceback.format_exc()
        print(f"\n[V4 Endpoint ERROR] {str(e)}")
        print(f"[V4 Endpoint ERROR] Full traceback:\n{error_trace}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing V4 debate: {str(e)}"
        )


@app.post("/api/generate-turn", response_model=GenerateTurnResponse)
async def generate_turn(request: GenerateTurnRequest):
    """
    Generate a single participant's turn in the debate.
    
    Used for interactive debates where turns are generated one at a time
    instead of running the full debate at once.
    """
    print(f"\n[Generate Turn] Participant: {request.participant.label}")
    print(f"[Generate Turn] Iteration: {request.iteration}")
    print(f"[Generate Turn] Max Iterations: {request.maxIterations}")
    
    try:
        # Build context from previous messages
        context_parts = []
        is_first_turn = not request.previousMessages or len(request.previousMessages) == 0
        # Check if this participant is a moderator
        is_moderator = 'moderator' in request.participant.role.lower()
        # Moderator summary happens AFTER all iterations complete (iteration > maxIterations)
        is_moderator_summary_turn = request.iteration > request.maxIterations and is_moderator
        
        if request.previousMessages:
            # Moderators need ALL messages (both intermediate and final turns) to synthesize discussion
            # Regular debaters only need last 3 messages for context efficiency
            if is_moderator:
                recent_messages = request.previousMessages  # ALL messages for moderator synthesis
            else:
                recent_messages = request.previousMessages[-3:]  # Last 3 messages only for regular debaters
            
            for msg in recent_messages:
                # For final summary, include full messages with special header
                # For moderator intermediate turns, include full messages with different header
                # For regular debaters, truncate long messages
                if is_moderator_summary_turn:
                    # Final summary - don't truncate, use complete transcript
                    context_parts.append(f"{msg.speaker}: {msg.content}")
                elif is_moderator:
                    # Intermediate moderator turn - include full content
                    context_parts.append(f"{msg.speaker}: {msg.content}")
                else:
                    # Regular debater - truncate long messages
                    content_preview = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
                    context_parts.append(f"{msg.speaker}: {content_preview}")
        
        # Generate response using facilitator's internal method
        from utils.ollama_client import OllamaClient
        from datetime import datetime
        
        ollama = OllamaClient()
        
        # Mode-specific role guidance (simplified for debates, not TwistedPair distortion)
        mode_guidance = {
            "echo_er": "Focus on positive aspects and opportunities. Amplify what's working.",
            "invert_er": "Challenge assumptions. Point out what's missing or contradictory.",
            "what_if_er": "Explore alternative scenarios. Ask 'what if' questions.",
            "so_what_er": "Question implications. Ask 'so what' and demand practical impact.",
            "cucumb_er": "Stay analytical and composed. Provide systematic analysis.",
            "archiv_er": "Connect to history and precedents. Provide context from past examples."
        }
        
        mode_hint = mode_guidance.get(request.participant.mode.value, "Provide your perspective.")
        tone_instruction = config.TONE_INSTRUCTIONS.get(request.participant.tone.value, "")
        
        # Check if this is a USER participant
        is_user = request.participant.model == 'USER'
        
        # Build prompt based on whether this is first turn, moderator summary, or regular turn
        if is_moderator_summary_turn and is_moderator and not is_user:
            # Final moderator summary
            context = "\n".join(context_parts) if context_parts else ""
            full_prompt = f"""You are {request.participant.label}, the moderator of this debate.

Topic: {request.topic}

Complete debate transcript:
{context}

This is the FINAL SUMMARY. Your job is to:
- Summarize EACH participant's key arguments (do NOT omit any participant)
- Identify points of agreement and disagreement across ALL participants
- Highlight the strongest points from each perspective
- Provide a brief but comprehensive conclusion without declaring a winner

IMPORTANT: Make sure to cover ALL participants who spoke. Do not leave anyone out.
IMPORTANT: Do NOT introduce yourself or use placeholder names. Jump straight into the summary.

Style: {tone_instruction}

Provide a comprehensive closing summary (MAX 200 words)."""
        elif is_first_turn:
            if is_moderator:
                # Moderator opening
                full_prompt = f"""You are {request.participant.label}, the moderator of this debate.

Topic: {request.topic}

This is the opening. Your job is to:
- Welcome the participants
- Clearly state the debate topic
- Explain the format briefly
- Invite participants to begin

Style: {tone_instruction}

IMPORTANT: Do NOT introduce yourself by name or use placeholder text like "[Your Name]". Your role is already displayed. Jump straight into your opening.

Provide a brief opening statement (MAX 100 words). Be welcoming and clear."""
            else:
                # Regular participant opening
                full_prompt = f"""You are {request.participant.label} in a debate.

Topic: {request.topic}

This is your opening statement. Present your initial perspective on the topic.

Your role: {mode_hint}
Style: {tone_instruction}

IMPORTANT: Do NOT introduce yourself by name or use placeholder text like "[Your Name]". Your identity is already displayed. Jump straight into your argument.

Provide a brief opening (MAX 100 words). Be specific and direct."""
        else:
            # Subsequent turns - respond to previous discussion
            context = "\n".join(context_parts)
            
            if is_moderator:
                full_prompt = f"""You are {request.participant.label}, the moderator of this debate.

Topic: {request.topic}

Full discussion so far:
{context}

Your job is to:
- Acknowledge key points made by EACH participant who has spoken
- Ask clarifying questions to explore ideas further
- Guide the discussion forward constructively

IMPORTANT: If multiple participants have spoken, acknowledge ALL of them. Don't skip anyone.
IMPORTANT: Do NOT introduce yourself or use placeholder names. Jump straight into moderation.

Style: {tone_instruction}

Provide brief moderation (MAX 100 words)."""
            else:
                # Check if this is many-on-one format to customize prompts
                is_examiner = 'examiner' in request.participant.role.lower() and 'examinee' not in request.participant.role.lower()
                is_examinee = 'examinee' in request.participant.role.lower()
                
                if is_examiner:
                    # Examiner questioning the examinee
                    full_prompt = f"""You are {request.participant.label}, an examiner in this examination.

Topic: {request.topic}

Recent discussion:
{context}

Your role: {mode_hint}
Style: {tone_instruction}

IMPORTANT: Do NOT introduce yourself or use placeholder names. Jump straight into your question or challenge.

Ask a probing question or present a challenge to the examinee's position. Be specific and critical (MAX 100 words)."""
                elif is_examinee:
                    # Examinee responding to examiners' questions
                    full_prompt = f"""You are {request.participant.label}, the examinee responding to examiners.

Topic: {request.topic}

Recent discussion:
{context}

Your role: {mode_hint}
Style: {tone_instruction}

IMPORTANT: Do NOT introduce yourself or use placeholder names. Jump straight into your response.

Respond to the examiners' questions and challenges. Defend or refine your position (MAX 100 words)."""
                else:
                    # Regular debate participant
                    full_prompt = f"""You are {request.participant.label} in a debate.

Topic: {request.topic}

Recent discussion:
{context}

Your role: {mode_hint}
Style: {tone_instruction}

IMPORTANT: Do NOT introduce yourself or use placeholder names. Jump straight into your response.

Respond to the points raised. Provide a brief response (MAX 100 words). Be specific and direct."""
        
        # Get Ollama parameters based on gain
        ollama_params = config.get_ollama_params(request.gain or 5)
        
        # Generate response
        response = ollama.generate(
            model=request.participant.model,
            prompt=full_prompt,
            **ollama_params
        )
        
        # Create message
        message = DebateMessage(
            speaker=request.participant.label,
            content=response,
            role=request.participant.role,
            iteration=request.iteration,
            timestamp=datetime.utcnow().isoformat()
        )
        
        return GenerateTurnResponse(
            message=message,
            success=True,
            error=None
        )
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"\n[Generate Turn ERROR] {str(e)}")
        print(f"[Generate Turn ERROR] Full traceback:\n{error_trace}")
        
        return GenerateTurnResponse(
            message=DebateMessage(
                speaker=request.participant.label,
                content=f"Error generating response: {str(e)}",
                role=request.participant.role,
                iteration=request.iteration,
                timestamp=datetime.utcnow().isoformat()
            ),
            success=False,
            error=str(e)
        )


@app.post("/api/analyze-debate", response_model=AnalyzeDebateResponse)
async def analyze_debate(request: AnalyzeDebateRequest):
    """
    Analyze debate messages and generate metrics using LLM.
    """
    print(f"\n[Analyze Debate] Analyzing {len(request.messages)} messages")
    print(f"[Analyze Debate] Iteration: {request.iteration}")
    
    try:
        from utils.ollama_client import OllamaClient
        
        ollama = OllamaClient()
        
        # Build conversation summary - include ALL messages with full content
        # We have 128K context window, so no need to truncate
        conversation = []
        for msg in request.messages:  # ALL messages
            speaker = msg.speaker
            content = msg.content  # Full content, no truncation
            conversation.append(f"{speaker}: {content}")
        
        conv_text = "\n\n".join(conversation)
        
        print(f"[Analyze Debate] Sending {len(request.messages)} messages ({len(conv_text)} chars) to {config.METRICS_MODEL}")
        
        # Create analysis prompt
        analysis_prompt = f"""You are analyzing a debate to generate metrics. Be objective and precise.

Topic: {request.topic}

Recent conversation:
{conv_text}

Analyze the debate and provide the following metrics in JSON format:

{{
  "agreementScore": <number 0-10, where 0=total disagreement, 10=complete agreement>,
  "convergenceStatus": "<CONVERGING or DIVERGING or STABLE>",
  "emotionalSensitivity": "<LOW or MEDIUM or HIGH>",
  "biasLevel": "<LOW or NEUTRAL or HIGH>",
  "topicDrift": "<LOW or MEDIUM or HIGH>"
}}

Analysis criteria:
- agreementScore: How much do participants agree on core points? Look for shared positions.
- convergenceStatus: Are positions getting closer (CONVERGING), further apart (DIVERGING), or staying same (STABLE)?
- emotionalSensitivity: Intensity of emotional language, charged words, personal attacks.
- biasLevel: Degree of one-sided arguments, partisan language, ignoring counterpoints.
- topicDrift: How much has discussion wandered from the original topic?

Respond ONLY with the JSON object, no explanation."""

        # Call LLM for analysis
        response = ollama.generate(
            model=config.METRICS_MODEL,
            prompt=analysis_prompt,
            temperature=0.3,  # Low temperature for consistent analysis
            top_p=0.8,
            top_k=20
        )
        
        print(f"[Analyze Debate] LLM Response: {response[:500]}...")  # First 500 chars
        
        # Parse JSON response
        import json
        import re
        
        # Extract JSON from response (in case LLM adds extra text)
        json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
        if json_match:
            metrics_data = json.loads(json_match.group())
            print(f"[Analyze Debate] Parsed metrics: {metrics_data}")
        else:
            print(f"[Analyze Debate] ERROR: Could not find JSON in response: {response}")
            raise ValueError("Could not parse metrics JSON from LLM response")
        
        # Import enum classes
        from app.models import ConvergenceStatus, SensitivityLevel, BiasLevel
        
        # Map string values to enums
        convergence_map = {
            "CONVERGING": ConvergenceStatus.CONVERGING,
            "DIVERGING": ConvergenceStatus.DIVERGING,
            "STABLE": ConvergenceStatus.STABLE
        }
        
        sensitivity_map = {
            "LOW": SensitivityLevel.LOW,
            "MEDIUM": SensitivityLevel.MEDIUM,
            "HIGH": SensitivityLevel.HIGH
        }
        
        bias_map = {
            "LOW": BiasLevel.LOW,
            "NEUTRAL": BiasLevel.NEUTRAL,
            "HIGH": BiasLevel.HIGH
        }
        
        # Create metrics object
        metrics = DebateMetrics(
            iteration=request.iteration,
            status="In Progress",
            agreementScore=float(metrics_data.get("agreementScore", 5.0)),
            convergenceStatus=convergence_map.get(
                metrics_data.get("convergenceStatus", "STABLE"),
                ConvergenceStatus.STABLE
            ),
            emotionalSensitivity=sensitivity_map.get(
                metrics_data.get("emotionalSensitivity", "LOW"),
                SensitivityLevel.LOW
            ),
            biasLevel=bias_map.get(
                metrics_data.get("biasLevel", "NEUTRAL"),
                BiasLevel.NEUTRAL
            ),
            topicDrift=sensitivity_map.get(
                metrics_data.get("topicDrift", "LOW"),
                SensitivityLevel.LOW
            )
        )
        
        print(f"[Analyze Debate] Final Metrics:")
        print(f"  - Agreement Score: {metrics.agreementScore}")
        print(f"  - Convergence Status: {metrics.convergenceStatus}")
        print(f"  - Emotional Sensitivity: {metrics.emotionalSensitivity}")
        print(f"  - Bias Level: {metrics.biasLevel}")
        print(f"  - Topic Drift: {metrics.topicDrift}")
        
        return AnalyzeDebateResponse(
            metrics=metrics,
            success=True,
            error=None
        )
        
    except Exception as e:
        import traceback
        print(f"\n[Analyze Debate ERROR] {str(e)}")
        print(traceback.format_exc())
        
        # Return baseline metrics on error
        from app.models import ConvergenceStatus, SensitivityLevel, BiasLevel
        
        return AnalyzeDebateResponse(
            metrics=DebateMetrics(
                iteration=request.iteration,
                status="In Progress",
                agreementScore=0.0,
                convergenceStatus=ConvergenceStatus.STABLE,
                emotionalSensitivity=SensitivityLevel.LOW,
                biasLevel=BiasLevel.NEUTRAL,
                topicDrift=SensitivityLevel.LOW
            ),
            success=False,
            error=str(e)
        )


# === OPTIONAL: User Input Endpoint (for interactive debates) ===

# In-memory storage for active debates (in production, use Redis or database)
active_debates = {}

@app.post("/api/save-debate")
async def save_debate_record(data: dict):
    """
    Save debate transcript to markdown file.
    """
    try:
        topic = data.get('topic', 'Untitled')
        format_type = data.get('format', 'debate')
        messages = data.get('messages', [])
        participants = data.get('participants', [])
        gain = data.get('gain', 5)
        timestamp = data.get('timestamp', datetime.utcnow().isoformat())
        
        # Generate filename
        safe_timestamp = timestamp.replace(':', '-').replace('.', '-')[:19]
        filename = f"debate_{format_type}_{safe_timestamp}.md"
        filepath = outputs_dir / filename
        
        # Build markdown content
        md_content = f"""# TwistedDebate V4 - {format_type.replace('-', ' ').title()}

**Topic:** {topic}

**Date:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

**Gain Level:** {gain}/10

## Participants

"""
        
        for p in participants:
            md_content += f"- **{p.get('label', 'Unknown')}**: {p.get('model', 'N/A')} ({p.get('mode', 'N/A')} mode, {p.get('tone', 'N/A')} tone)\n"
        
        md_content += "\n---\n\n## Transcript\n\n"
        
        for msg in messages:
            speaker = msg.get('speaker', 'Unknown')
            content = msg.get('content', '')
            iteration = msg.get('iteration', '')
            turn_label = f" [Turn {iteration}]" if iteration else ""
            
            md_content += f"### {speaker}{turn_label}\n\n{content}\n\n---\n\n"
        
        md_content += f"\n\n*Generated by TwistedDebate V4*\n"
        
        # Save file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        print(f"[Save Debate] Saved to: {filepath}")
        
        return {
            "success": True,
            "filename": filename,
            "path": f"/outputs/{filename}",
            "url": f"/outputs/{filename}"
        }
        
    except Exception as e:
        import traceback
        print(f"[Save Debate ERROR] {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Error saving debate: {str(e)}"
        )

@app.post("/api/user-input")
async def submit_user_input(debate_id: str, participant_id: str, content: str):
    """
    Submit user input for an active debate.
    
    This endpoint would be used when USER is a participant.
    """
    # TODO: Implement user input handling
    # This would involve:
    # 1. Looking up the active debate
    # 2. Validating the participant
    # 3. Adding the user's message
    # 4. Continuing the debate
    # 5. Returning updated state
    
    raise HTTPException(
        status_code=501,
        detail="User input not yet implemented - coming soon!"
    )


if __name__ == "__main__":
    import uvicorn
    
    # Print configuration summary
    config.print_config_summary()
    
    print("\nStarting TwistedDebate V4 server...")
    print(f"Access the web UI at: http://{config.SERVER_HOST}:{config.SERVER_PORT}")
    print(f"API documentation at: http://{config.SERVER_HOST}:{config.SERVER_PORT}/docs")
    print("\nPress Ctrl+C to stop the server.\n")
    
    uvicorn.run(
        app,
        host=config.SERVER_HOST,
        port=config.SERVER_PORT,
        reload=config.RELOAD
    )
