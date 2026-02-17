"""
facilitator.py - Core logic for TwistedDebate V4

Orchestrates debates in multiple formats:
- One-to-One Debate
- Cross-Examination
- Many-on-One Examination
- Panel Discussion with Moderator
- Round Robin Discussion
"""

import sys
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.ollama_client import OllamaClient, OllamaConnectionError, OllamaGenerationError
from app.models import (
    DebateFormat,
    ParticipantConfig,
    DebateMessage,
    DebateMetrics,
    KeyStatement,
    DebateAnalysis,
    ConvergenceStatus,
    SensitivityLevel,
    BiasLevel
)
from app import config


class Facilitator:
    """
    Orchestrates V4 multi-format debates.
    """
    
    def __init__(
        self,
        ollama_url: str = None,
        default_model: str = None,
        verbose: bool = False
    ):
        """
        Initialize Facilitator V4.
        
        Args:
            ollama_url: URL of Ollama server
            default_model: Default model for generation
            verbose: Enable debug logging
        """
        if ollama_url is None:
            ollama_url = config.OLLAMA_URL
        if default_model is None:
            default_model = config.DEFAULT_MODEL
            
        self.ollama_url = ollama_url
        self.verbose = verbose
        
        # Initialize Ollama client
        self.ollama_client = OllamaClient(
            base_url=ollama_url,
            default_model=default_model,
            verbose=verbose
        )
        
        self._log("Facilitator V4 initialized (multi-format debate system)")
    
    def _log(self, message: str):
        """Print log message if verbose."""
        if self.verbose:
            print(f"[Facilitator] {message}")
    
    def check_health(self) -> Dict[str, bool]:
        """
        Check health of dependencies.
        
        Returns:
            Dict with ollama_available
        """
        ollama_healthy = self.ollama_client.is_healthy()
        
        if ollama_healthy:
            models = self.ollama_client.list_models()
            self._log(f"Ollama is healthy. Available models: {len(models)}")
        else:
            self._log("Ollama health check failed")
        
        return {
            "ollama_available": ollama_healthy
        }
    
    def list_ollama_models(self) -> List[str]:
        """
        List available Ollama models.
        
        Returns:
            List of model names
        """
        try:
            return self.ollama_client.list_models()
        except Exception as e:
            self._log(f"Error listing models: {e}")
            return config.FALLBACK_MODELS
    
    # === CORE DEBATE ORCHESTRATION ===
    
    def run_debate(
        self,
        topic: str,
        format: DebateFormat,
        participants: List[ParticipantConfig],
        max_iterations: int = 10,
        gain: int = 5
    ) -> Dict[str, Any]:
        """
        Run a complete debate based on format.
        
        Args:
            topic: Debate topic
            format: Debate format
            participants: List of participant configurations
            max_iterations: Maximum debate iterations
            gain: Debate intensity (1-10)
            
        Returns:
            Dict with debate results including messages, metrics, key statements
        """
        self._log(f"Starting {format.value} debate on topic: {topic[:50]}...")
        self._log(f"Participants: {len(participants)}, Max iterations: {max_iterations}, Gain: {gain}")
        
        # Route to appropriate format handler
        if format == DebateFormat.ONE_TO_ONE:
            return self._run_one_to_one_debate(topic, participants, max_iterations, gain)
        elif format == DebateFormat.CROSS_EXAM:
            return self._run_cross_examination(topic, participants, max_iterations, gain)
        elif format == DebateFormat.MANY_ON_ONE:
            return self._run_many_on_one(topic, participants, max_iterations, gain)
        elif format == DebateFormat.PANEL:
            return self._run_panel_discussion(topic, participants, max_iterations, gain)
        elif format == DebateFormat.ROUND_ROBIN:
            return self._run_round_robin(topic, participants, max_iterations, gain)
        else:
            raise ValueError(f"Unsupported debate format: {format}")
    
    # === FORMAT-SPECIFIC HANDLERS ===
    
    def _run_one_to_one_debate(
        self,
        topic: str,
        participants: List[ParticipantConfig],
        max_iterations: int,
        gain: int
    ) -> Dict[str, Any]:
        """
        Run a one-to-one debate between two participants.
        
        Args:
            topic: Debate topic
            participants: List of 2 participants
            max_iterations: Maximum exchanges
            gain: Intensity
            
        Returns:
            Debate results
        """
        self._log("[One-to-One] Starting debate")
        
        if len(participants) != 2:
            raise ValueError("One-to-one debate requires exactly 2 participants")
        
        messages = []
        key_statements = []
        
        debater1 = participants[0]
        debater2 = participants[1]
        
        # Check for USER participation
        has_user = debater1.model == "USER" or debater2.model == "USER"
        
        # Initialize context
        previous_context = ""
        opponent_statement = ""
        
        for iteration in range(1, max_iterations + 1):
            self._log(f"[One-to-One] Iteration {iteration}/{max_iterations}")
            
            # Debater 1's turn
            if debater1.model != "USER":
                response1 = self._generate_one_to_one_response(
                    participant=debater1,
                    topic=topic,
                    opponent=debater2,
                    opponent_statement=opponent_statement,
                    previous_context=previous_context,
                    gain=gain
                )
                
                msg1 = DebateMessage(
                    speaker=debater1.label,
                    content=response1,
                    role=debater1.role,
                    iteration=iteration,
                    timestamp=datetime.utcnow().isoformat()
                )
                messages.append(msg1)
                opponent_statement = response1
                previous_context = self._build_context(messages[-3:])
            else:
                # USER turn - return placeholder, frontend will handle
                msg1 = DebateMessage(
                    speaker=debater1.label,
                    content="[Awaiting user input]",
                    role="user-pending",
                    iteration=iteration,
                    timestamp=datetime.utcnow().isoformat()
                )
                messages.append(msg1)
                break  # Stop here and wait for user input
            
            # Debater 2's turn
            if debater2.model != "USER":
                response2 = self._generate_one_to_one_response(
                    participant=debater2,
                    topic=topic,
                    opponent=debater1,
                    opponent_statement=opponent_statement,
                    previous_context=previous_context,
                    gain=gain
                )
                
                msg2 = DebateMessage(
                    speaker=debater2.label,
                    content=response2,
                    role=debater2.role,
                    iteration=iteration,
                    timestamp=datetime.utcnow().isoformat()
                )
                messages.append(msg2)
                opponent_statement = response2
                previous_context = self._build_context(messages[-3:])
            else:
                # USER turn
                msg2 = DebateMessage(
                    speaker=debater2.label,
                    content="[Awaiting user input]",
                    role="user-pending",
                    iteration=iteration,
                    timestamp=datetime.utcnow().isoformat()
                )
                messages.append(msg2)
                break
            
            # Extract key statements every few iterations
            if iteration % 2 == 0:
                key_statements.extend(self._extract_key_statements(messages[-4:], iteration))
        
        # Analyze final state
        metrics = self._analyze_debate(topic, messages, iteration)
        
        return {
            "topic": topic,
            "format": DebateFormat.ONE_TO_ONE,
            "participants": participants,
            "messages": messages,
            "metrics": metrics,
            "keyStatements": key_statements,
            "completed": not has_user or iteration >= max_iterations,
            "convergenceReached": metrics.agreementScore >= config.CONVERGENCE_THRESHOLD if metrics.agreementScore else False
        }
    
    def _run_cross_examination(
        self,
        topic: str,
        participants: List[ParticipantConfig],
        max_iterations: int,
        gain: int
    ) -> Dict[str, Any]:
        """Run cross-examination format."""
        self._log("[Cross-Exam] Starting examination")
        
        if len(participants) != 2:
            raise ValueError("Cross-examination requires exactly 2 participants (examiner and examinee)")
        
        examiner = participants[0]
        examinee = participants[1]
        
        messages = []
        key_statements = []
        
        # Examinee's initial statement
        initial_statement = self._generate_with_mode_tone(
            prompt=f"State your position on: {topic}",
            participant=examinee,
            gain=gain
        )
        
        messages.append(DebateMessage(
            speaker=examinee.label,
            content=initial_statement,
            role=examinee.role,
            iteration=0,
            timestamp=datetime.utcnow().isoformat()
        ))
        
        # Examination rounds
        for iteration in range(1, max_iterations + 1):
            self._log(f"[Cross-Exam] Round {iteration}/{max_iterations}")
            
            # Examiner asks question
            question_prompt = config.CROSS_EXAMINATION_PROMPT.format(
                participant_name=examiner.label,
                role=examiner.role,
                mode=examiner.mode.value,
                tone=examiner.tone.value,
                topic=topic,
                previous_context=self._build_context(messages[-3:]),
                other_perspective=messages[-1].content,
                instruction="Generate a probing question or challenge to the examinee's position."
            )
            
            question = self._generate_with_params(question_prompt, examiner.model, gain)
            
            messages.append(DebateMessage(
                speaker=examiner.label,
                content=question,
                role=examiner.role,
                iteration=iteration,
                timestamp=datetime.utcnow().isoformat()
            ))
            
            # Examinee responds
            response_prompt = config.CROSS_EXAMINATION_PROMPT.format(
                participant_name=examinee.label,
                role=examinee.role,
                mode=examinee.mode.value,
                tone=examinee.tone.value,
                topic=topic,
                previous_context=self._build_context(messages[-3:]),
                other_perspective=question,
                instruction="Respond to the examiner's question or challenge. Defend or refine your position."
            )
            
            response = self._generate_with_params(response_prompt, examinee.model, gain)
            
            messages.append(DebateMessage(
                speaker=examinee.label,
                content=response,
                role=examinee.role,
                iteration=iteration,
                timestamp=datetime.utcnow().isoformat()
            ))
        
        metrics = self._analyze_debate(topic, messages, max_iterations)
        key_statements = self._extract_key_statements(messages, max_iterations)
        
        return {
            "topic": topic,
            "format": DebateFormat.CROSS_EXAM,
            "participants": participants,
            "messages": messages,
            "metrics": metrics,
            "keyStatements": key_statements,
            "completed": True,
            "convergenceReached": False  # Not applicable for cross-exam
        }
    
    def _run_many_on_one(
        self,
        topic: str,
        participants: List[ParticipantConfig],
        max_iterations: int,
        gain: int
    ) -> Dict[str, Any]:
        """Run many-on-one examination format."""
        self._log("[Many-on-One] Starting examination")
        
        # First participant is the examinee, rest are examiners
        examinee = participants[0]
        examiners = participants[1:]
        
        self._log(f"[Many-on-One] {len(examiners)} examiners vs 1 examinee")
        
        messages = []
        key_statements = []
        
        # Examinee's initial statement
        initial_statement = self._generate_with_mode_tone(
            prompt=f"State your position on: {topic}",
            participant=examinee,
            gain=gain
        )
        
        messages.append(DebateMessage(
            speaker=examinee.label,
            content=initial_statement,
            role=examinee.role,
            iteration=0,
            timestamp=datetime.utcnow().isoformat()
        ))
        
        # Examination rounds
        for iteration in range(1, max_iterations + 1):
            self._log(f"[Many-on-One] Round {iteration}/{max_iterations}")
            
            # Each examiner asks a question
            for examiner in examiners:
                question_prompt = config.MANY_ON_ONE_PROMPT.format(
                    participant_name=examiner.label,
                    role=examiner.role,
                    mode=examiner.mode.value,
                    tone=examiner.tone.value,
                    topic=topic,
                    previous_context=self._build_context(messages[-5:]),
                    current_situation=f"Examinee's current position: {messages[-1].content[:200]}...",
                    instruction="Ask a probing question or present a challenge."
                )
                
                question = self._generate_with_params(question_prompt, examiner.model, gain)
                
                messages.append(DebateMessage(
                    speaker=examiner.label,
                    content=question,
                    role=examiner.role,
                    iteration=iteration,
                    timestamp=datetime.utcnow().isoformat()
                ))
            
            # Examinee responds to all questions
            all_questions = "\n\n".join([
                f"{msg.speaker}: {msg.content}"
                for msg in messages[-(len(examiners)):]
            ])
            
            response_prompt = config.MANY_ON_ONE_PROMPT.format(
                participant_name=examinee.label,
                role=examinee.role,
                mode=examinee.mode.value,
                tone=examinee.tone.value,
                topic=topic,
                previous_context=self._build_context(messages[-10:]),
                current_situation=f"Questions from examiners:\n{all_questions}",
                instruction="Respond to all examiners' questions and challenges."
            )
            
            response = self._generate_with_params(response_prompt, examinee.model, gain)
            
            messages.append(DebateMessage(
                speaker=examinee.label,
                content=response,
                role=examinee.role,
                iteration=iteration,
                timestamp=datetime.utcnow().isoformat()
            ))
        
        metrics = self._analyze_debate(topic, messages, max_iterations)
        key_statements = self._extract_key_statements(messages, max_iterations)
        
        return {
            "topic": topic,
            "format": DebateFormat.MANY_ON_ONE,
            "participants": participants,
            "messages": messages,
            "metrics": metrics,
            "keyStatements": key_statements,
            "completed": True,
            "convergenceReached": False
        }
    
    def _run_panel_discussion(
        self,
        topic: str,
        participants: List[ParticipantConfig],
        max_iterations: int,
        gain: int
    ) -> Dict[str, Any]:
        """Run panel discussion with moderator format."""
        self._log("[Panel] Starting discussion")
        
        # First participant is moderator, rest are panelists
        moderator = participants[0]
        panelists = participants[1:]
        
        self._log(f"[Panel] 1 moderator + {len(panelists)} panelists")
        
        messages = []
        key_statements = []
        
        has_user_moderator = moderator.model == "USER"
        
        # Moderator opens discussion
        if not has_user_moderator:
            opening = self._generate_moderator_opening(topic, moderator, gain)
            messages.append(DebateMessage(
                speaker=moderator.label,
                content=opening,
                role=moderator.role,
                iteration=0,
                timestamp=datetime.utcnow().isoformat()
            ))
        else:
            messages.append(DebateMessage(
                speaker=moderator.label,
                content="[Awaiting moderator opening]",
                role="user-pending",
                iteration=0,
                timestamp=datetime.utcnow().isoformat()
            ))
            # Would need to wait for user input here
        
        # Discussion rounds
        for iteration in range(1, max_iterations + 1):
            self._log(f"[Panel] Round {iteration}/{max_iterations}")
            
            # Each panelist contributes
            for panelist in panelists:
                statement_prompt = config.PANEL_DISCUSSION_PROMPT.format(
                    participant_name=panelist.label,
                    role=panelist.role,
                    mode=panelist.mode.value,
                    tone=panelist.tone.value,
                    topic=topic,
                    moderator_guidance=messages[0].content if messages else "",
                    previous_statements=self._build_context(messages[-5:]),
                    instruction="Share your perspective and respond to others' points."
                )
                
                statement = self._generate_with_params(statement_prompt, panelist.model, gain)
                
                messages.append(DebateMessage(
                    speaker=panelist.label,
                    content=statement,
                    role=panelist.role,
                    iteration=iteration,
                    timestamp=datetime.utcnow().isoformat()
                ))
            
            # Moderator summarizes/guides (every other round)
            if iteration % 2 == 0 and not has_user_moderator:
                moderation = self._generate_moderator_summary(
                    topic, messages[-len(panelists):], moderator, gain
                )
                
                messages.append(DebateMessage(
                    speaker=moderator.label,
                    content=moderation,
                    role=moderator.role,
                    iteration=iteration,
                    timestamp=datetime.utcnow().isoformat()
                ))
        
        metrics = self._analyze_debate(topic, messages, max_iterations)
        key_statements = self._extract_key_statements(messages, max_iterations)
        
        return {
            "topic": topic,
            "format": DebateFormat.PANEL,
            "participants": participants,
            "messages": messages,
            "metrics": metrics,
            "keyStatements": key_statements,
            "completed": not has_user_moderator or iteration >= max_iterations,
            "convergenceReached": metrics.agreementScore >= config.CONVERGENCE_THRESHOLD if metrics.agreementScore else False
        }
    
    def _run_round_robin(
        self,
        topic: str,
        participants: List[ParticipantConfig],
        max_iterations: int,
        gain: int
    ) -> Dict[str, Any]:
        """Run round-robin discussion format."""
        self._log("[Round Robin] Starting discussion")
        self._log(f"[Round Robin] {len(participants)} participants")
        
        messages = []
        key_statements = []
        
        # Round-robin iterations
        for iteration in range(1, max_iterations + 1):
            self._log(f"[Round Robin] Round {iteration}/{max_iterations}")
            
            # Each participant speaks in turn
            for participant in participants:
                statement_prompt = config.ROUND_ROBIN_PROMPT.format(
                    participant_name=participant.label,
                    mode=participant.mode.value,
                    tone=participant.tone.value,
                    topic=topic,
                    previous_statements=self._build_context(messages[-len(participants):])
                )
                
                statement = self._generate_with_params(statement_prompt, participant.model, gain)
                
                messages.append(DebateMessage(
                    speaker=participant.label,
                    content=statement,
                    role=participant.role,
                    iteration=iteration,
                    timestamp=datetime.utcnow().isoformat()
                ))
        
        metrics = self._analyze_debate(topic, messages, max_iterations)
        key_statements = self._extract_key_statements(messages, max_iterations)
        
        return {
            "topic": topic,
            "format": DebateFormat.ROUND_ROBIN,
            "participants": participants,
            "messages": messages,
            "metrics": metrics,
            "keyStatements": key_statements,
            "completed": True,
            "convergenceReached": metrics.agreementScore >= config.CONVERGENCE_THRESHOLD if metrics.agreementScore else False
        }
    
    # === HELPER METHODS ===
    
    def _generate_one_to_one_response(
        self,
        participant: ParticipantConfig,
        topic: str,
        opponent: ParticipantConfig,
        opponent_statement: str,
        previous_context: str,
        gain: int
    ) -> str:
        """Generate a response in one-to-one debate."""
        prompt = config.ONE_TO_ONE_DEBATE_PROMPT.format(
            participant_name=participant.label,
            role=participant.role,
            mode=participant.mode.value,
            tone=participant.tone.value,
            topic=topic,
            previous_context=previous_context,
            opponent_name=opponent.label,
            opponent_statement=opponent_statement or "(Opening statement)"
        )
        
        return self._generate_with_params(prompt, participant.model, gain)
    
    def _generate_with_mode_tone(
        self,
        prompt: str,
        participant: ParticipantConfig,
        gain: int
    ) -> str:
        """Generate text with mode and tone applied."""
        mode_prompt = config.MODE_PROMPTS[participant.mode.value].format(text=prompt)
        tone_instruction = config.TONE_INSTRUCTIONS[participant.tone.value]
        
        full_prompt = f"{mode_prompt}\n\n{tone_instruction}"
        
        return self._generate_with_params(full_prompt, participant.model, gain)
    
    def _generate_with_params(
        self,
        prompt: str,
        model: str,
        gain: int
    ) -> str:
        """Generate text using Ollama with gain-based parameters."""
        params = config.get_ollama_params(gain)
        
        try:
            result = self.ollama_client.generate(
                prompt=prompt,
                model=model,
                **params
            )
            return result
        except Exception as e:
            self._log(f"Generation error: {e}")
            return f"[Error generating response: {str(e)}]"
    
    def _generate_moderator_opening(
        self,
        topic: str,
        moderator: ParticipantConfig,
        gain: int
    ) -> str:
        """Generate moderator's opening statement."""
        prompt = config.MODERATOR_PROMPT.format(
            topic=topic,
            previous_statements="",
            instruction="Open the panel discussion. Introduce the topic and set the tone for productive dialogue."
        )
        
        return self._generate_with_params(prompt, moderator.model, gain)
    
    def _generate_moderator_summary(
        self,
        topic: str,
        recent_messages: List[DebateMessage],
        moderator: ParticipantConfig,
        gain: int
    ) -> str:
        """Generate moderator's summary/guidance."""
        previous_statements = "\n\n".join([
            f"{msg.speaker}: {msg.content[:200]}..."
            for msg in recent_messages
        ])
        
        prompt = config.MODERATOR_PROMPT.format(
            topic=topic,
            previous_statements=previous_statements,
            instruction="Summarize key points, identify areas of agreement/disagreement, and guide the next phase of discussion."
        )
        
        return self._generate_with_params(prompt, moderator.model, gain)
    
    def _build_context(self, messages: List[DebateMessage]) -> str:
        """Build context string from recent messages."""
        if not messages:
            return "(No previous context)"
        
        return "\n\n".join([
            f"{msg.speaker}: {msg.content[:300]}..."
            for msg in messages
        ])
    
    def _analyze_debate(
        self,
        topic: str,
        messages: List[DebateMessage],
        iteration: int
    ) -> DebateMetrics:
        """
        Analyze debate state and generate metrics.
        
        This is a simplified version - in production you'd use an LLM to analyze.
        """
        # Simplified metrics generation
        agreementScore = min(5.0 + (iteration * 0.5), 10.0)  # Gradually increases
        
        return DebateMetrics(
            iteration=iteration,
            status="In Progress" if iteration < config.MAX_DEBATE_ITERATIONS else "Completed",
            agreementScore=agreementScore,
            convergenceStatus=ConvergenceStatus.CONVERGING if agreementScore > 7 else ConvergenceStatus.DIVERGING,
            emotionalSensitivity=SensitivityLevel.MEDIUM,
            biasLevel=BiasLevel.NEUTRAL,
            topicDrift=SensitivityLevel.LOW
        )
    
    def _extract_key_statements(
        self,
        messages: List[DebateMessage],
        iteration: int
    ) -> List[KeyStatement]:
        """Extract key statements from messages."""
        # Simplified - just take first sentence of each message
        statements = []
        for msg in messages:
            first_sentence = msg.content.split('.')[0] + '.'
            if len(first_sentence) > 20:  # Only if meaningful
                statements.append(KeyStatement(
                    speaker=msg.speaker,
                    text=first_sentence[:100],
                    iteration=iteration
                ))
        return statements
