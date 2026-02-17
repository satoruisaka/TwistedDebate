# TwistedDebate - Autonomous LLM Debate System

A modern, full-stack debate platform with progressive turn-by-turn generation, LLM-based metrics analysis, and support for multiple debate formats. Built with vanilla JavaScript frontend and FastAPI backend.

## Overview

TwistedDebate provides a clean, intuitive interface for conducting AI-powered debates with various formats:
- **One-on-One Debate**: Two perspectives in direct debate
- **Cross-Examination**: One examiner questioning an examinee
- **Many-on-One Examination**: Multiple examiners questioning one examinee  
- **Panel Discussion**: Multiple panelists with a moderator
- **Round Robin**: Multiple participants in turn-based discussion

### Key Features
- **Progressive Display**: Turn-by-turn generation with real-time updates
- **USER Participation**: Join debates as a human participant
- **LLM-Based Metrics**: AI analysis of debate quality using gemma3:27b
- **Moderator Synthesis**: Intelligent summarization covering all participants
- **Markdown Export**: Save complete debate records
- **128K Context Window**: Full conversation history for all analysis
- **Thinking Indicators**: Visual feedback during LLM generation
- **Gain Control**: Adjust response creativity (1-10 scale)

## 🏗️ Architecture

### Technology Stack
- **Frontend**: Vanilla JavaScript (ES6+ modules)
- **Styling**: CSS3 with CSS Variables for theming
- **Markdown Rendering**: Marked.js
- **Backend**: FastAPI with Pydantic validation
- **LLM Interface**: Direct Ollama API client
- **Distortion**: TwistedPair-inspired modes (6) and tones (5)
- **Metrics Model**: gemma3:27b for debate analysis

### Progressive Turn-by-Turn Architecture
Unlike batch processing, V4 uses a turn-by-turn approach:
1. **Frontend loops** through participants for each iteration
2. **For each turn**: Call `/api/generate-turn` endpoint
3. **Moderators receive ALL messages** (full context for synthesis)
4. **Regular debaters receive last 3 messages** (efficiency)
5. **After each full iteration**: Call `/api/analyze-debate` for metrics
6. **After all iterations**: Moderator generates final summary
7. **Display updates progressively** as each participant responds

This approach provides:
- Real-time visibility of debate progression
- Better UX with thinking indicators
- Support for USER participation (input box appears when needed)
- Accurate metrics updated after each turn
- Comprehensive moderator summaries (no participant omissions)

### Component-Based Structure
The application uses a modular architecture:
- **AppState**: Centralized state management
- **FormatConfigs**: Debate format definitions
- **Dynamic Configuration**: Auto-generated participant forms
- **Event-Driven**: Clean separation of concerns

## 📁 File Structure

```
TwistedDebate/v4/
├── app/
│   ├── __init__.py         # App initialization
│   ├── config.py           # Configuration, prompts, model settings
│   ├── models.py           # Pydantic data models & enums
│   ├── facilitator.py      # Debate orchestration (legacy)
│   └── server.py           # FastAPI application & endpoints
├── utils/
│   ├── __init__.py
│   └── ollama_client.py    # Direct Ollama API client
├── static/
│   ├── index.html          # Web UI structure (3-column layout)
│   ├── styles.css          # Responsive styling with dark/light themes
│   └── app.js              # Frontend logic (1069 lines: progressive mode, USER input)
├── outputs/                # Saved debate records (markdown)
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
├── startTwistedDebate_v4.sh  # Startup script
└── README.md              # This file
```

## 🎨 Features

### User Interface
- **Responsive 3-Column Layout**
  - Left Sidebar: Configuration panel (collapsible)
  - Center: Debate transcript area
  - Right Sidebar: Progress metrics (collapsible)

- **Dark/Light Theme Toggle**
  - CSS variable-based theming
  - Persistent theme preference
  - Toggle button in header

- **Dynamic Configuration**
  - Format-specific participant forms
  - Auto-generated fields based on format selection
  - Smooth show/hide transitions

### Debate Formats

#### 1. One-to-One Debate
- Two debaters with configurable:
  - LLM model (including USER option)
  - Distortion mode
  - Tone variation

#### 2. Cross-Examination  
- Examiner and examinee
- No USER participation
- Full configuration per participant

#### 3. Many-on-One Examination
- 2-6 examiners
- 1 examinee
- Individual configuration for each examiner
- No USER participation

#### 4. Panel Discussion
- 1-6 panelists
- 1 moderator (can be USER)
- Individual configuration per panelist

#### 5. Round Robin
- 2-6 participants
- No moderator
- No USER participation
- Equal configuration for all

### Moderator Intelligence

V4 features smart moderator synthesis designed to prevent participant omissions:

**Context Management:**
- **Moderators receive ALL messages** from debate start (not just last 3)
- Ensures comprehensive awareness of every participant's contributions
- Applies to both intermediate turns AND final summary

**Intermediate Turns:**
- Moderator acknowledges key points from EACH participant who spoke
- Asks clarifying questions to explore ideas further
- Guides discussion forward constructively
- Prompt explicitly instructs: "If multiple participants have spoken, acknowledge ALL of them"

**Final Summary:**
- Triggered after all iterations complete
- Receives complete untruncated debate transcript
- Summarizes EACH participant's key arguments (no one left out)
- Identifies points of agreement/disagreement across ALL perspectives
- Word limit increased to 200 (vs 100 for regular turns) for comprehensive coverage

**Implementation Details:**
- Detection: `iteration > maxIterations` triggers final summary mode
- Context: Full `msg.content` instead of truncated previews
- Prompting: Explicit instructions to cover every participant
- Quality: Fixed bug where panelists were marked "(No specific argument presented)"

### Progress Tracking & Metrics

#### Real-Time LLM-Based Metrics
After each full iteration, the system sends ALL messages to gemma3:27b for objective analysis:

- **Agreement Score** (0-10): How much participants agree on core points
- **Convergence Status**: Are positions getting closer (CONVERGING), further apart (DIVERGING), or staying same (STABLE)?
- **Emotional Sensitivity** (Low/Medium/High): Intensity of emotional language, charged words, personal attacks
- **Bias Level** (Low/Neutral/High): Degree of one-sided arguments, partisan language, ignoring counterpoints
- **Topic Drift** (Low/Medium/High): How much discussion has wandered from original topic

**Analysis Configuration:**
- Model: gemma3:27b (configurable via `METRICS_MODEL` in config.py)
- Context: ALL messages with full content (128K context window)
- Temperature: 0.3 (low for consistent analysis)
- Updates: After each complete turn iteration
- Baseline: All metrics start at 0/Low/Neutral

#### Key Statements
- Extracted automatically from each participant's first sentence per turn
- Displayed in right sidebar for quick reference
- Updates progressively as debate proceeds

#### Debate Records
- Complete markdown files saved to `/outputs/`
- Includes: headers, topic, participants, full transcript, timestamps
- Clickable links provided after debate completion
- Files named: `debate_YYYY-MM-DD_HHMMSS.md`

## 🔌 API Endpoints

### Core Endpoints

- **GET `/health`** - System health check
- **GET `/api/models`** - List available Ollama models
- **GET `/api/config`** - Get distortion modes and tones

### Progressive Debate Endpoints

- **POST `/api/generate-turn`** - Generate single participant turn
  - Request: participant config, previous messages, topic, iteration
  - Response: single DebateMessage with content
  - Context logic: Moderators receive ALL messages, debaters receive last 3
  - Handles: first turn opening, regular turns, final moderator summary

- **POST `/api/analyze-debate`** - Analyze debate for metrics
  - Request: topic, all messages, iteration number
  - Response: DebateMetrics (agreement, convergence, sensitivity, bias, drift)
  - Uses: gemma3:27b with temperature 0.3
  - Context: ALL messages with full content (no truncation)

- **POST `/api/save-debate`** - Save debate record as markdown
  - Request: debate format, topic, participants, messages
  - Response: filename, path, URL for download
  - Saves to: `/outputs/debate_YYYY-MM-DD_HHMMSS.md`

- **GET `/api/records/{filename}`** - Retrieve saved debate record

**Interactive API docs:** http://localhost:8004/docs

## 🚀 Quick Start

### Prerequisites

1. **Ollama** must be running:
   ```bash
   ollama serve
   ```

2. **Python 3.10+** installed

3. **Required Ollama models**:
   ```bash
   # For debate generation (any model works)
   ollama pull llama2
   # or
   ollama pull qwen3:latest
   
   # For metrics analysis (required)
   ollama pull gemma3:27b
   ```

### Starting the Application

```bash
cd /home/sator/project/TwistedDebate/v4
./startTwistedDebate_v4.sh
```

This will:
- Create virtual environment (if needed)
- Install dependencies (FastAPI, Pydantic, Uvicorn, python-dotenv, requests)
- Start the FastAPI backend on port 8004
- Serve the web UI

**Access at:** http://localhost:8004

### Configuration Steps

1. **Enter Debate Topic**: Type your question or topic
2. **Select Format**: Choose from 5 debate formats
3. **Set Max Iterations**: Number of rounds (default: 5)
4. **Adjust Gain**: Response creativity slider (1-10, default: 5)
   - 1-3: Low creativity (temp 0.3-0.5)
   - 4-7: Medium creativity (temp 0.7-0.9)
   - 8-10: High creativity (temp 1.1-1.5)
5. **Configure Participants**: 
   - Select LLM models (or USER for manual input)
   - Choose distortion mode (echo_er, invert_er, what_if_er, so_what_er, cucumb_er, archiv_er)
   - Select tone variation (analytical, creative, contrarian, diplomatic, provocative)
6. **Start Debate**: Click "Start Debate" button
7. **Monitor Progress**: 
   - Watch "X is thinking..." indicators during generation
   - View metrics updated after each turn
   - See key statements extracted in real-time
8. **Participate** (if USER selected): 
   - Input box appears in center panel when it's your turn
   - Enter response and press Ctrl+Enter or click Submit
   - LLM generates responses for other participants
9. **Save Results**: 
   - Debate auto-saves to markdown when complete
   - Click record file link to download

## 🎨 Theming

### CSS Variables
All colors and dimensions use CSS variables for easy customization:

```css
:root {
  --bg-primary: #1a1a2e;
  --text-primary: #eaeaea;
  --accent-primary: #4a9eff;
  /* ... more variables */
}
```

### Theme Toggle
- Click moon/sun icon in header
- Preference saved to localStorage
- Instant theme switching

### Custom Themes
To add custom themes:
1. Define new CSS class (e.g., `.my-theme`)
2. Override CSS variables
3. Update `applyTheme()` in app.js

## 📱 Responsive Design

- **Desktop** (>1200px): Full 3-column layout
- **Tablet** (768-1200px): Narrower sidebars
- **Mobile** (<768px): Stacked layout, collapsible sections

## 🔧 Customization

### Adding New Debate Formats
Edit `FormatConfigs` in app.js:
```javascript
'my-format': {
    label: 'My Custom Format',
    participants: [
        { role: 'participant1', label: 'Participant 1', allowUser: true },
        // ...
    ]
}
```

### Modifying Participant Options
Configuration is fetched from backend `/api/config`, allowing dynamic updates without code changes.

## 🐛 Debugging

Access debug utilities via browser console:
```javascript
// View current state
window.TwistedDebateApp.state

// Add test message
window.TwistedDebateApp.addMessage('Test', 'Message content', 'user')

// Update progress
window.TwistedDebateApp.updateProgress({ agreementScore: 8 })
```

### Logging & Diagnostics

**Backend Logs** (terminal running uvicorn):
- `[Generate Turn]` - Shows participant, iteration, max iterations
- `[Analyze Debate]` - Shows message count, char count, model used
- `[Analyze Debate] LLM Response:` - First 500 chars of metrics response
- `[Analyze Debate] Parsed metrics:` - JSON data from LLM
- `[Analyze Debate] Final Metrics:` - All 5 computed values

**Browser Console** (F12 Developer Tools):
- `Metrics response:` - Full API response from `/api/analyze-debate`
- `Updating UI with metrics:` - Data being sent to UI update function
- Network tab shows all API calls with timing

## 🔧 Troubleshooting

### Metrics Not Updating

**Symptom:** Metrics stuck at 0/Low/Neutral baseline values

**Common Causes:**
1. **Enum mismatch**: Check that LLM response values match enum definitions in `models.py`
   - `BiasLevel` must have: LOW, NEUTRAL, HIGH (not SLIGHTLY_POSITIVE, etc.)
   - Check terminal logs for `[Analyze Debate ERROR]` with AttributeError
2. **JSON parsing failure**: LLM might not return valid JSON
   - Check `[Analyze Debate] LLM Response:` in terminal
   - Verify JSON structure matches expected format
3. **Frontend not receiving data**: Check browser console
   - Should see `Metrics response: {success: true, metrics: {...}}`
   - If missing, check Network tab for failed API calls

**Fix:** Update enums in `models.py` to match prompt expectations, or vice versa

### Moderator Omitting Participants

**Symptom:** Final summary shows "(No specific argument presented)" for participants who actually spoke

**Common Causes:**
1. **Context limitation**: Moderator only receiving last N messages instead of all
   - Check `is_moderator` detection in `server.py`
   - Verify context logic: `recent_messages = request.previousMessages if is_moderator else ...`
2. **Truncated content**: Messages cut off before reaching LLM
   - Ensure no `content[:300]` truncation for moderator turns
3. **Incomplete prompt context**: Not all participants included in prompt

**Fix:** Moderators should always receive ALL messages with full content (no truncation)

### Thinking Indicators Not Clearing

**Symptom:** "X is thinking..." persists after response appears

**Cause:** `clearThinkingMessages()` not called in error path

**Fix:** Ensure `finally` block calls `clearThinkingMessages()` in all async functions

### USER Input Box Not Appearing

**Symptom:** When USER selected, no input box shows during debate

**Causes:**
1. Format doesn't allow USER (`allowUser: false` in FormatConfigs)
2. USER detection failing (`participant.model !== 'USER'`)
3. Progressive mode not enabled

**Fix:** Check participant config and ensure progressive mode is active

## 📝 Implementation Notes

### Framework Choice
- **Vanilla JavaScript** chosen for:
  - No build process required
  - Consistent with MRA and TwistedDebate v3
  - Fast load times
  - Easy deployment

### State Management
- Centralized `AppState` object
- Event-driven updates
- No external dependencies

### Component Pattern
- Functions as components
- Dynamic DOM generation
- Reusable form builders

## ✅ Completed Features

- [x] FastAPI backend server with progressive turn-by-turn architecture
- [x] Ollama integration with direct API client
- [x] All 5 debate formats (one-to-one, cross-exam, many-on-one, panel, round-robin)
- [x] USER participation support with input box and Ctrl+Enter
- [x] LLM-based debate analysis and metrics (gemma3:27b)
- [x] Markdown export of debate transcripts
- [x] Thinking indicators ("X is thinking...", "Updating debate metrics...")
- [x] Gain control slider (1-10 scale) with real-time descriptions
- [x] Key statements extraction (first sentence per message)
- [x] Moderator synthesis with full context (no participant omissions)
- [x] 128K context window for complete debate history
- [x] Dark/light theme toggle with localStorage persistence
- [x] Progressive metrics updates after each turn
- [x] Collapsible sidebars for responsive layout

## 🚧 Future Enhancements

- [ ] WebSocket support for streaming responses
- [ ] Toast notification system for better UX feedback
- [ ] PDF export (currently markdown only)
- [ ] Debate history/replay functionality with database
- [ ] Advanced metrics visualization (charts, graphs)
- [ ] Multi-language support (i18n)
- [ ] Accessibility improvements (ARIA labels, keyboard shortcuts)
- [ ] Database persistence (currently in-memory only)
- [ ] Debate templates and presets
- [ ] Export to other formats (JSON, HTML)

## 🤝 Integration with Existing System

TwistedDebate V4 integrates with:
- **Ollama** (required): Local LLM model serving on port 11434
- **TwistedPair** (inspired): Distortion modes (6) and tones (5) based on TwistedPair's pedal metaphor
- **MRA_v3** (consistent): Vanilla JS architecture pattern, no build tools

**GPU Management:**
- `OLLAMA_KEEP_ALIVE = 0`: Releases GPU memory immediately after generation
- `NUM_CTX = 128000`: 128K context window for full conversation history

## 📄 License

Same as parent TwistedDebate project.

---

**Built with ❤️ for the TwistedDebate project**

**Built with ❤️ for the TwistedDebate project**