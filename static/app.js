/**
 * TwistedDebate V4 - Main Application Logic
 * 
 * Handles:
 * - Format selection and dynamic configuration
 * - Ollama model fetching
 * - Debate execution and display
 * - User interaction
 * - Theme toggling
 */

// ================================
// Application State
// ================================
const AppState = {
    models: [],
    config: {
        modes: [],
        tones: []
    },
    currentFormat: 'one-to-one',
    participants: [],
    debate: {
        active: false,
        iteration: 0,
        transcript: [],
        metrics: {
            agreementScore: null,
            convergenceStatus: null,
            emotionalSensitivity: null,
            biasLevel: null,
            topicDrift: null
        }
    },
    userRole: null,
    theme: 'dark'
};

// ================================
// Configuration Templates
// ================================
const FormatConfigs = {
    'one-to-one': {
        label: 'One-to-One Debate',
        participants: [
            { role: 'debater1', label: 'Debater 1', allowUser: true },
            { role: 'debater2', label: 'Debater 2', allowUser: true }
        ]
    },
    'cross-exam': {
        label: 'One-on-One Cross-Examination',
        participants: [
            { role: 'examiner', label: 'Examiner', allowUser: false },
            { role: 'examinee', label: 'Examinee', allowUser: false }
        ]
    },
    'many-on-one': {
        label: 'Many-on-One Examination',
        participants: [
            { role: 'examinee', label: 'Examinee', allowUser: false },
            { role: 'examiners', label: 'Examiners', count: { min: 2, max: 6 }, allowUser: false }
        ]
    },
    'panel': {
        label: 'Panel Discussion with Moderator',
        participants: [
            { role: 'moderator', label: 'Moderator', allowUser: true },
            { role: 'panelists', label: 'Panelists', count: { min: 1, max: 6 }, allowUser: false }
        ]
    },
    'round-robin': {
        label: 'Round Robin without Moderator',
        participants: [
            { role: 'participants', label: 'Participants', count: { min: 2, max: 6 }, allowUser: false }
        ]
    }
};

// ================================
// Initialization
// ================================
document.addEventListener('DOMContentLoaded', async () => {
    console.log('TwistedDebate V4 Initializing...');
    
    // Load saved theme
    loadTheme();
    
    // Setup event listeners
    setupEventListeners();
    
    // Load configuration from backend
    await loadConfiguration();
    
    // Initialize participant config for default format
    updateParticipantConfig();
    
    console.log('TwistedDebate V4 Ready');
});

// ================================
// Event Listeners
// ================================
function setupEventListeners() {
    // Theme toggle
    document.getElementById('theme-toggle').addEventListener('click', toggleTheme);
    
    // Help button
    document.getElementById('help-btn').addEventListener('click', showHelp);
    
    // License link
    document.getElementById('show-license').addEventListener('click', (e) => {
        e.preventDefault();
        showLicense();
    });
    
    // Sidebar collapse
    document.getElementById('config-collapse').addEventListener('click', () => toggleSidebar('left'));
    document.getElementById('progress-collapse').addEventListener('click', () => toggleSidebar('right'));
    
    // Format selection
    document.querySelectorAll('input[name="debate-format"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            AppState.currentFormat = e.target.value;
            updateParticipantConfig();
        });
    });
    
    // Start debate button
    document.getElementById('start-debate-btn').addEventListener('click', startDebate);
    
    // Gain slider
    document.getElementById('gain-slider').addEventListener('input', (e) => {
        const gain = e.target.value;
        document.getElementById('gain-value').textContent = gain;
        updateGainDescription(gain);
    });
    
    // User input submission
    document.getElementById('submit-user-input').addEventListener('click', submitUserInput);
    
    // Enter key in user input
    document.getElementById('user-input').addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'Enter') {
            submitUserInput();
        }
    });
}

// ================================
// Configuration Loading
// ================================
async function loadConfiguration() {
    try {
        // Load Ollama models
        console.log('Fetching Ollama models...');
        const modelsResponse = await fetch('/api/models');
        const modelsData = await modelsResponse.json();
        AppState.models = modelsData.models || [];
        console.log(`Loaded ${AppState.models.length} models`);
        
        // Load distortion modes and tones from config
        console.log('Fetching configuration...');
        const configResponse = await fetch('/api/config');
        const configData = await configResponse.json();
        AppState.config.modes = configData.modes || [];
        AppState.config.tones = configData.tones || [];
        console.log(`Loaded ${AppState.config.modes.length} modes, ${AppState.config.tones.length} tones`);
        
    } catch (error) {
        console.error('Error loading configuration:', error);
        // Fallback to defaults
        AppState.models = ['llama2', 'mistral', 'mixtral'];
        AppState.config.modes = ['echo_er', 'invert_er', 'what_if_er', 'so_what_er', 'cucumb_er', 'archiv_er'];
        AppState.config.tones = ['neutral', 'technical', 'primal', 'poetic', 'satirical'];
        
        showNotification('Using default configuration (backend not available)', 'warning');
    }
}

// ================================
// Dynamic Participant Configuration
// ================================
function updateParticipantConfig() {
    const container = document.getElementById('participant-config');
    const format = FormatConfigs[AppState.currentFormat];
    
    if (!format) return;
    
    container.innerHTML = '';
    container.classList.add('fade-in');
    
    const title = document.createElement('h3');
    title.textContent = 'Participants';
    container.appendChild(title);
    
    format.participants.forEach(participant => {
        if (participant.count) {
            // Multiple participants with count
            createMultiParticipantConfig(container, participant);
        } else {
            // Single participant
            createSingleParticipantConfig(container, participant);
        }
    });
}

function createSingleParticipantConfig(container, participant) {
    const card = document.createElement('div');
    card.className = 'participant-card';
    
    const title = document.createElement('h4');
    title.textContent = participant.label;
    card.appendChild(title);
    
    // Model selection
    const modelGroup = createFormGroup('LLM Model', 'select');
    const modelSelect = modelGroup.querySelector('select');
    modelSelect.id = `${participant.role}-model`;
    
    // Add USER option if allowed
    if (participant.allowUser) {
        const userOption = document.createElement('option');
        userOption.value = 'USER';
        userOption.textContent = 'USER (Manual Input)';
        modelSelect.appendChild(userOption);
    }
    
    // Add model options
    AppState.models.forEach(model => {
        const option = document.createElement('option');
        option.value = model;
        option.textContent = model;
        modelSelect.appendChild(option);
    });
    
    card.appendChild(modelGroup);
    
    // Distortion mode
    const modeGroup = createFormGroup('Distortion Mode', 'select');
    const modeSelect = modeGroup.querySelector('select');
    modeSelect.id = `${participant.role}-mode`;
    AppState.config.modes.forEach(mode => {
        const option = document.createElement('option');
        option.value = mode;
        option.textContent = mode.replace(/_/g, '-').toUpperCase();
        modeSelect.appendChild(option);
    });
    card.appendChild(modeGroup);
    
    // Tone variation
    const toneGroup = createFormGroup('Tone Variation', 'select');
    const toneSelect = toneGroup.querySelector('select');
    toneSelect.id = `${participant.role}-tone`;
    AppState.config.tones.forEach(tone => {
        const option = document.createElement('option');
        option.value = tone;
        option.textContent = tone.charAt(0).toUpperCase() + tone.slice(1);
        toneSelect.appendChild(option);
    });
    card.appendChild(toneGroup);
    
    container.appendChild(card);
}

function createMultiParticipantConfig(container, participant) {
    const card = document.createElement('div');
    card.className = 'participant-card';
    
    const title = document.createElement('h4');
    title.textContent = participant.label;
    card.appendChild(title);
    
    // Count selection
    const countGroup = createFormGroup(`Number of ${participant.label}`, 'number');
    const countInput = countGroup.querySelector('input');
    countInput.id = `${participant.role}-count`;
    countInput.min = participant.count.min;
    countInput.max = participant.count.max;
    countInput.value = participant.count.min;
    countInput.addEventListener('change', () => {
        updateMultiParticipantDetails(participant.role, parseInt(countInput.value));
    });
    card.appendChild(countGroup);
    
    // Container for individual participant configs
    const detailsContainer = document.createElement('div');
    detailsContainer.id = `${participant.role}-details`;
    card.appendChild(detailsContainer);
    
    container.appendChild(card);
    
    // Initialize with minimum count
    updateMultiParticipantDetails(participant.role, participant.count.min);
}

function updateMultiParticipantDetails(role, count) {
    const container = document.getElementById(`${role}-details`);
    container.innerHTML = '';
    
    for (let i = 1; i <= count; i++) {
        const subCard = document.createElement('div');
        subCard.style.marginTop = '1rem';
        subCard.style.paddingTop = '1rem';
        subCard.style.borderTop = `1px solid var(--border-color)`;
        
        const subTitle = document.createElement('strong');
        subTitle.textContent = `${role.charAt(0).toUpperCase() + role.slice(1, -1)} ${i}`;
        subTitle.style.display = 'block';
        subTitle.style.marginBottom = '0.75rem';
        subTitle.style.color = 'var(--text-primary)';
        subCard.appendChild(subTitle);
        
        // Model
        const modelGroup = createFormGroup('Model', 'select');
        const modelSelect = modelGroup.querySelector('select');
        modelSelect.id = `${role}-${i}-model`;
        AppState.models.forEach(model => {
            const option = document.createElement('option');
            option.value = model;
            option.textContent = model;
            modelSelect.appendChild(option);
        });
        subCard.appendChild(modelGroup);
        
        // Mode
        const modeGroup = createFormGroup('Mode', 'select');
        const modeSelect = modeGroup.querySelector('select');
        modeSelect.id = `${role}-${i}-mode`;
        AppState.config.modes.forEach(mode => {
            const option = document.createElement('option');
            option.value = mode;
            option.textContent = mode.replace(/_/g, '-').toUpperCase();
            modeSelect.appendChild(option);
        });
        subCard.appendChild(modeGroup);
        
        // Tone
        const toneGroup = createFormGroup('Tone', 'select');
        const toneSelect = toneGroup.querySelector('select');
        toneSelect.id = `${role}-${i}-tone`;
        AppState.config.tones.forEach(tone => {
            const option = document.createElement('option');
            option.value = tone;
            option.textContent = tone.charAt(0).toUpperCase() + tone.slice(1);
            toneSelect.appendChild(option);
        });
        subCard.appendChild(toneGroup);
        
        container.appendChild(subCard);
    }
}

function createFormGroup(label, type) {
    const group = document.createElement('div');
    group.className = 'form-group';
    
    const labelEl = document.createElement('label');
    labelEl.textContent = label;
    group.appendChild(labelEl);
    
    if (type === 'select') {
        const select = document.createElement('select');
        group.appendChild(select);
    } else if (type === 'number') {
        const input = document.createElement('input');
        input.type = 'number';
        group.appendChild(input);
    }
    
    return group;
}

// ================================
// Debate Control
// ================================
async function startDebate() {
    const topic = document.getElementById('debate-topic').value.trim();
    
    if (!topic) {
        showNotification('Please enter a debate topic', 'error');
        return;
    }
    
    // Collect participant configuration
    const participants = collectParticipants();
    const gain = parseInt(document.getElementById('gain-slider').value);
    const maxIterations = parseInt(document.getElementById('max-iterations').value);
    
    // Check if USER is participating
    const userParticipant = participants.find(p => p.model === 'USER');
    if (userParticipant) {
        AppState.userRole = userParticipant.role;
    }
    
    // Update UI
    document.getElementById('current-topic').textContent = topic;
    clearTranscript();
    resetProgress();
    
    // Clear previous debate context
    AppState.debate.messages = [];
    AppState.debate.transcript = [];
    AppState.debate.iteration = 0;
    AppState.debate.active = false;
    
    // Update button state
    const btn = document.getElementById('start-debate-btn');
    btn.disabled = true;
    btn.innerHTML = '<span class="loading-indicator"><span class="spinner"></span> Starting debate...</span>';
    
    // Start debate process
    AppState.debate.active = true;
    AppState.participants = participants;
    
    // Show initial thinking message
    addThinkingMessage('Initializing debate...');
    
    // Use progressive mode for better UX (shows messages as they're generated)
    // If USER is participating, must use progressive mode
    const useProgressiveMode = true;  // Always use progressive for better UX
    
    if (useProgressiveMode || userParticipant) {
        if (userParticipant) {
            showNotification('Interactive mode: USER input enabled', 'info');
        }
        simulateDebate(topic, participants, true);  // True = use real LLM via API
        btn.disabled = false;
        btn.innerHTML = '<span class="btn-text">Start Debate</span>';
        return;
    }
    
    // Legacy mode: Call backend API for full debate (returns all at once)
    try {
        const response = await fetch('/api/debate-v4', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                topic: topic,
                format: AppState.currentFormat,
                participants: participants,
                maxIterations: maxIterations,
                gain: gain
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        processDebateResponse(data);
        
    } catch (error) {
        console.error('Debate error:', error);
        showNotification(`Error: ${error.message}`, 'error');
        
        // Demo mode - simulate debate
        simulateDebate(topic, participants);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<span class="btn-text">Start Debate</span>';
    }
}

function collectParticipants() {
    const format = FormatConfigs[AppState.currentFormat];
    const participants = [];
    
    format.participants.forEach(participant => {
        if (participant.count) {
            // Multiple participants
            const count = parseInt(document.getElementById(`${participant.role}-count`).value);
            for (let i = 1; i <= count; i++) {
                participants.push({
                    role: `${participant.role.slice(0, -1)}_${i}`,
                    label: `${participant.label.slice(0, -1)} ${i}`,
                    model: document.getElementById(`${participant.role}-${i}-model`).value,
                    mode: document.getElementById(`${participant.role}-${i}-mode`).value,
                    tone: document.getElementById(`${participant.role}-${i}-tone`).value
                });
            }
        } else {
            // Single participant
            participants.push({
                role: participant.role,
                label: participant.label,
                model: document.getElementById(`${participant.role}-model`).value,
                mode: document.getElementById(`${participant.role}-mode`).value,
                tone: document.getElementById(`${participant.role}-tone`).value
            });
        }
    });
    
    return participants;
}

// ================================
// Debate Simulation (Demo Mode)
// ================================
async function simulateDebate(topic, participants, isInteractive = false) {
    // Only show backend unavailable message if not in interactive mode
    if (!isInteractive) {
        showNotification('Demo Mode: Simulating debate (backend not available)', 'warning');
    }
    
    const maxIterations = parseInt(document.getElementById('max-iterations').value);
    const gain = parseInt(document.getElementById('gain-slider').value);
    
    addMessage('System', `Debate started ${isInteractive ? 'in interactive mode' : 'in demo mode'} (${maxIterations} turns, gain ${gain})`, 'system', 0);
    
    // Initialize with baseline metrics
    updateProgress({
        iteration: 0,
        status: 'Starting',
        agreementScore: 0,
        convergenceStatus: 'Stable',
        emotionalSensitivity: 'Low',
        biasLevel: 'Neutral',
        topicDrift: 'Low'
    });
    
    // Special handling for many-on-one: Examinee gives opening statement before main loop
    if (AppState.currentFormat === 'many-on-one') {
        const examinee = participants.find(p => p.role.includes('examinee'));
        if (examinee) {
            addThinkingMessage(`${examinee.label} is preparing opening statement...`);
            
            if (isInteractive) {
                try {
                    const response = await fetch('/api/generate-turn', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            topic: topic,
                            participant: examinee,
                            previousMessages: [],
                            iteration: 0,
                            maxIterations: maxIterations,
                            gain: gain
                        })
                    });
                    
                    if (response.ok) {
                        const data = await response.json();
                        if (data.success && data.message) {
                            addMessage(data.message.speaker, data.message.content, data.message.role, 0);
                            if (!AppState.debate.messages) AppState.debate.messages = [];
                            AppState.debate.messages.push(data.message);
                            
                            const firstSentence = data.message.content.split(/[.!?]/)[0].trim();
                            const keyText = firstSentence.length > 100 ? firstSentence.substring(0, 97) + '...' : firstSentence;
                            addKeyStatement(data.message.speaker, keyText, 0);
                        }
                    }
                } catch (error) {
                    console.error('Opening statement error:', error);
                    const message = `[Error: Could not generate opening statement. ${error.message}]`;
                    addMessage(examinee.label, message, examinee.role, 0);
                }
            } else {
                // Demo mode
                await sleep(800);
                const message = `This is my opening position on "${topic.substring(0, 100)}..." [Opening Statement]`;
                addMessage(examinee.label, message, examinee.role, 0);
            }
            
            clearThinkingMessages();
            await sleep(300);
        }
    }
    
    // Simulate debate rounds
    for (let i = 1; i <= maxIterations; i++) {
        // Update iteration number
        updateProgress({
            iteration: i,
            status: 'In Progress'
        });
        
        for (const participant of participants) {
            if (participant.model === 'USER') {
                // Wait for user input
                addThinkingMessage(`Awaiting input from ${participant.label}...`);
                await waitForUserInput(participant, i);
                clearThinkingMessages();
            } else {
                // Show thinking message
                addThinkingMessage(`${participant.label} is thinking...`);
                
                // Generate real LLM response if interactive mode, otherwise simulate
                if (isInteractive) {
                    try {
                        // Get previous messages from AppState
                        const previousMessages = AppState.debate.messages || [];
                        
                        // Call backend to generate this turn
                        const response = await fetch('/api/generate-turn', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                topic: topic,
                                participant: participant,
                                previousMessages: previousMessages,
                                iteration: i,
                                maxIterations: maxIterations,
                                gain: gain
                            })
                        });
                        
                        if (!response.ok) {
                            throw new Error(`HTTP ${response.status}`);
                        }
                        
                        const data = await response.json();
                        
                        if (data.success && data.message) {
                            addMessage(data.message.speaker, data.message.content, data.message.role, i);
                            // Store message in AppState for context
                            if (!AppState.debate.messages) AppState.debate.messages = [];
                            AppState.debate.messages.push(data.message);
                            
                            // Extract key statement (first sentence or up to 100 chars)
                            const firstSentence = data.message.content.split(/[.!?]/)[0].trim();
                            const keyText = firstSentence.length > 100 ? firstSentence.substring(0, 97) + '...' : firstSentence;
                            addKeyStatement(data.message.speaker, keyText, i);
                        } else {
                            throw new Error(data.error || 'Generation failed');
                        }
                        
                    } catch (error) {
                        console.error('Turn generation error:', error);
                        clearThinkingMessages();
                        showNotification(`Error generating ${participant.label}'s response: ${error.message}`, 'error');
                        // Fallback to demo message
                        const message = `[Error: Could not generate response. ${error.message}]`;
                        addMessage(participant.label, message, participant.role, i);
                    }
                } else {
                    // Demo mode - show simulated response
                    await sleep(800 + Math.random() * 400);  // Simulate thinking time
                    const message = `This is a simulated response from ${participant.label} using ${participant.model} in ${participant.mode} mode with ${participant.tone} tone. [Turn ${i}/${maxIterations}]\n\nI'm addressing the topic: "${topic.substring(0, 100)}..."\n\nBased on the ${participant.mode} perspective, I believe we should consider this angle carefully.`;
                    addMessage(participant.label, message, participant.role, i);
                }
                
                clearThinkingMessages();
                await sleep(200);  // Brief pause between participants
            }
        }
        
        await sleep(300);  // Pause between participants
        
        // Analyze debate and update metrics after each full turn (if interactive mode)
        if (isInteractive && AppState.debate.messages && AppState.debate.messages.length > 0) {
            addThinkingMessage('Updating debate metrics...');
            
            try {
                const response = await fetch('/api/analyze-debate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        topic: topic,
                        messages: AppState.debate.messages,
                        iteration: i
                    })
                });
                
                if (response.ok) {
                    const data = await response.json();
                    console.log('Metrics response:', data);
                    if (data.success && data.metrics) {
                        console.log('Updating UI with metrics:', data.metrics);
                        updateProgress(data.metrics);
                    } else {
                        console.warn('Metrics analysis failed or no metrics returned');
                    }
                } else {
                    console.error('Metrics API returned error:', response.status);
                }
            } catch (error) {
                console.error('Metrics calculation error:', error);
            } finally {
                clearThinkingMessages();
            }
        }
    }
    
    // After all iterations complete, give moderator a final summary turn (if moderator exists and is not USER)
    const moderator = participants.find(p => p.role.toLowerCase().includes('moderator'));
    if (moderator && moderator.model !== 'USER' && isInteractive) {
        addThinkingMessage(`${moderator.label} is preparing final summary...`);
        
        try {
            const previousMessages = AppState.debate.messages || [];
            const summaryIteration = maxIterations + 1;
            
            const response = await fetch('/api/generate-turn', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    topic: topic,
                    participant: moderator,
                    previousMessages: previousMessages,
                    iteration: summaryIteration,
                    maxIterations: maxIterations,
                    gain: gain
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                
                if (data.success && data.message) {
                    addMessage(data.message.speaker, data.message.content, data.message.role, summaryIteration);
                    if (!AppState.debate.messages) AppState.debate.messages = [];
                    AppState.debate.messages.push(data.message);
                    
                    const firstSentence = data.message.content.split(/[.!?]/)[0].trim();
                    const keyText = firstSentence.length > 100 ? firstSentence.substring(0, 97) + '...' : firstSentence;
                    addKeyStatement(data.message.speaker, keyText, summaryIteration);
                }
            }
        } catch (error) {
            console.error('Moderator summary error:', error);
        }
        
        clearThinkingMessages();
        await sleep(300);
    }
    
    updateProgress({ status: 'Completed', iteration: maxIterations });
    const completionMsg = isInteractive ? 'Debate completed' : 'Demo debate completed';
    showNotification(completionMsg, 'success');
    
    // Save debate record to file
    if (isInteractive) {
        try {
            const response = await fetch('/api/save-debate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    topic: topic,
                    format: AppState.currentFormat,
                    messages: AppState.debate.messages || [],
                    participants: participants,
                    gain: gain,
                    timestamp: new Date().toISOString()
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                updateRecordInfo({
                    filename: data.filename,
                    path: data.path,
                    url: data.url
                });
                showNotification('Debate record saved', 'success');
            } else {
                console.error('Failed to save debate record');
            }
        } catch (error) {
            console.error('Error saving debate:', error);
        }
    }
}

function waitForUserInput(participant, iteration) {
    return new Promise((resolve) => {
        const inputArea = document.getElementById('user-input-area');
        const roleLabel = document.getElementById('user-role-label');
        const submitBtn = document.getElementById('submit-user-input');
        const userInput = document.getElementById('user-input');
        
        roleLabel.textContent = `(${participant.label} - Turn ${iteration})`;
        inputArea.classList.remove('hidden');
        userInput.focus();
        
        const handleSubmit = () => {
            const input = userInput.value.trim();
            if (input) {
                addMessage(participant.label, input, 'user', iteration);
                userInput.value = '';
                inputArea.classList.add('hidden');
                submitBtn.removeEventListener('click', handleSubmit);
                resolve();
            } else {
                showNotification('Please enter your response', 'error');
            }
        };
        
        // Handle both button click and Enter key
        submitBtn.addEventListener('click', handleSubmit);
        
        // Also handle Ctrl+Enter in the textarea
        const handleKeyDown = (e) => {
            if (e.ctrlKey && e.key === 'Enter') {
                handleSubmit();
                userInput.removeEventListener('keydown', handleKeyDown);
            }
        };
        userInput.addEventListener('keydown', handleKeyDown);
    });
}

function submitUserInput() {
    // Trigger submit (handled by waitForUserInput)
    document.getElementById('submit-user-input').click();
}

// ================================
// Message Display
// ================================
function clearTranscript() {
    const container = document.getElementById('transcript');
    container.innerHTML = '';
    
    // Also clear key statements and record info
    const statementsContainer = document.getElementById('key-statements');
    if (statementsContainer) statementsContainer.innerHTML = '';
    
    const recordContainer = document.getElementById('record-info');
    if (recordContainer) recordContainer.innerHTML = '';
}

function addMessage(speaker, content, role = '', iteration = null) {
    const container = document.getElementById('transcript');
    
    // Remove welcome message if present
    const welcome = container.querySelector('.welcome-message');
    if (welcome) welcome.remove();
    
    // Remove thinking messages
    clearThinkingMessages();
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'debate-message';
    
    if (role === 'user') {
        messageDiv.classList.add('user-message');
    } else if (role.includes('moderator')) {
        messageDiv.classList.add('moderator-message');
    }
    
    const header = document.createElement('div');
    header.className = 'message-header';
    
    const speakerSpan = document.createElement('span');
    speakerSpan.className = 'speaker-name';
    speakerSpan.textContent = speaker;
    
    const timestamp = document.createElement('span');
    timestamp.className = 'message-timestamp';
    const timeText = new Date().toLocaleTimeString();
    
    // Special handling for moderator summary turn (iteration > configured max)
    let turnLabel = '';
    if (iteration) {
        const configuredMax = parseInt(document.getElementById('max-iterations')?.value || 5);
        if (iteration > configuredMax && role.includes('moderator')) {
            turnLabel = 'Final Summary';
        } else {
            turnLabel = `Turn ${iteration}`;
        }
        timestamp.textContent = `${turnLabel} • ${timeText}`;
    } else {
        timestamp.textContent = timeText;
    }
    
    header.appendChild(speakerSpan);
    header.appendChild(timestamp);
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = renderMarkdown(content);
    
    messageDiv.appendChild(header);
    messageDiv.appendChild(contentDiv);
    
    container.appendChild(messageDiv);
    container.scrollTop = container.scrollHeight;
}

function renderMarkdown(text) {
    if (typeof marked !== 'undefined') {
        try {
            return marked.parse(text);
        } catch (e) {
            console.error('Markdown error:', e);
        }
    }
    return escapeHtml(text).replace(/\n/g, '<br>');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ================================
// Progress Updates
// ================================
function resetProgress() {
    updateProgress({
        iteration: 0,
        status: 'Not Started',
        agreementScore: '-',
        convergenceStatus: '-',
        emotionalSensitivity: '-',
        biasLevel: '-',
        topicDrift: '-'
    });
    
    document.getElementById('key-statements').innerHTML = '<p class="empty-state">No statements yet</p>';
    document.getElementById('record-info').innerHTML = '<p class="empty-state">No record file yet</p>';
}

function updateProgress(data) {
    if (data.iteration !== undefined) {
        document.getElementById('iteration-number').textContent = data.iteration;
    }
    if (data.status) {
        document.getElementById('debate-status').textContent = data.status;
    }
    if (data.agreementScore !== undefined) {
        document.getElementById('agreement-score').textContent = data.agreementScore;
    }
    if (data.convergenceStatus) {
        document.getElementById('convergence-status').textContent = data.convergenceStatus;
    }
    if (data.emotionalSensitivity) {
        document.getElementById('emotional-sensitivity').textContent = data.emotionalSensitivity;
    }
    if (data.biasLevel) {
        document.getElementById('bias-level').textContent = data.biasLevel;
    }
    if (data.topicDrift) {
        document.getElementById('topic-drift').textContent = data.topicDrift;
    }
}

function processDebateResponse(data) {
    // Clear any thinking messages
    clearThinkingMessages();
    
    // Process real backend response
    if (data.messages) {
        data.messages.forEach(msg => {
            addMessage(msg.speaker, msg.content, msg.role, msg.iteration);
        });
    }
    
    if (data.metrics) {
        updateProgress(data.metrics);
    }
    
    if (data.keyStatements) {
        updateKeyStatements(data.keyStatements);
    }
    
    if (data.recordFile) {
        updateRecordInfo(data.recordFile);
    }
}

function updateKeyStatements(statements) {
    const container = document.getElementById('key-statements');
    container.innerHTML = '';
    
    statements.forEach(stmt => {
        const div = document.createElement('div');
        div.className = 'statement-item';
        
        const speaker = document.createElement('span');
        speaker.className = 'statement-speaker';
        speaker.textContent = stmt.speaker;
        
        const text = document.createTextNode(`: ${stmt.text}`);
        
        div.appendChild(speaker);
        div.appendChild(text);
        container.appendChild(div);
    });
}

function addKeyStatement(speaker, text, iteration) {
    // Add a single key statement (for progressive mode)
    const container = document.getElementById('key-statements');
    
    const div = document.createElement('div');
    div.className = 'statement-item';
    
    const speakerSpan = document.createElement('span');
    speakerSpan.className = 'statement-speaker';
    speakerSpan.textContent = speaker;
    
    const textNode = document.createTextNode(`: ${text}`);
    
    div.appendChild(speakerSpan);
    div.appendChild(textNode);
    container.appendChild(div);
    
    // Auto-scroll to latest statement
    container.scrollTop = container.scrollHeight;
}

function updateRecordInfo(recordFile) {
    const container = document.getElementById('record-info');
    container.innerHTML = `
        <div style="margin-bottom: 0.5rem;"><strong>File:</strong> ${recordFile.filename}</div>
        <div style="margin-bottom: 0.5rem;"><strong>Location:</strong> ${recordFile.path}</div>
        <a href="${recordFile.url}" target="_blank">View Record</a>
    `;
}

// ================================
// UI Controls
// ================================
function toggleSidebar(side) {
    const sidebar = side === 'left' 
        ? document.getElementById('config-panel')
        : document.getElementById('progress-panel');
    
    sidebar.classList.toggle('collapsed');
    
    // Update collapse button arrow and aria-label
    const btn = side === 'left'
        ? document.getElementById('config-collapse')
        : document.getElementById('progress-collapse');
    
    const arrow = btn.querySelector('span');
    const isCollapsed = sidebar.classList.contains('collapsed');
    
    if (side === 'left') {
        arrow.textContent = isCollapsed ? '▶' : '◀';
        btn.setAttribute('aria-label', isCollapsed ? 'Expand configuration panel' : 'Collapse configuration panel');
    } else {
        arrow.textContent = isCollapsed ? '◀' : '▶';
        btn.setAttribute('aria-label', isCollapsed ? 'Expand progress panel' : 'Collapse progress panel');
    }
}

function toggleTheme() {
    AppState.theme = AppState.theme === 'dark' ? 'light' : 'dark';
    applyTheme();
    localStorage.setItem('twisteddebate-theme', AppState.theme);
}

function loadTheme() {
    const saved = localStorage.getItem('twisteddebate-theme');
    if (saved) {
        AppState.theme = saved;
    }
    applyTheme();
}

function applyTheme() {
    const icon = document.querySelector('.theme-icon');
    if (AppState.theme === 'light') {
        document.body.classList.add('light-theme');
        icon.textContent = '☀️';
    } else {
        document.body.classList.remove('light-theme');
        icon.textContent = '🌙';
    }
}

function showHelp() {
    const container = document.getElementById('transcript');
    container.innerHTML = `
        <div class="help-content">
            <h3>How to Use TwistedDebate</h3>
            <p class="help-intro">Autonomous LLM debate system with multiple formats, perspectives, and personalities</p>
            
            <div class="help-section">
                <h4>Quick Start Guide</h4>
                <ol>
                    <li><strong>Enter a Topic:</strong> Type your debate topic or question in the text area at the top left</li>
                    <li><strong>Choose Format:</strong> Select one of five debate formats:
                        <ul>
                            <li><strong>One-to-One:</strong> Direct debate between two perspectives</li>
                            <li><strong>Cross-Examination:</strong> One examiner questions one examinee</li>
                            <li><strong>Many-on-One:</strong> Multiple examiners question a single examinee</li>
                            <li><strong>Panel Discussion:</strong> Multiple perspectives with a moderator</li>
                            <li><strong>Round Robin:</strong> Turn-based discussion without a moderator</li>
                        </ul>
                    </li>
                    <li><strong>Configure Participants:</strong> For each participant, set:
                        <ul>
                            <li><strong>Model:</strong> Select an AI model or <code>USER</code> to participate yourself</li>
                            <li><strong>Mode:</strong> Thinking style (echo_er, invert_er, what_if_er, so_what_er, cucumb_er, archiv_er)</li>
                            <li><strong>Tone:</strong> Communication style (neutral, technical, primal, poetic, satirical)</li>
                        </ul>
                    </li>
                    <li><strong>Set Intensity:</strong> Adjust the Gain slider (1-10) to control debate passion and engagement</li>
                    <li><strong>Set Maximum Turns:</strong> Choose how many rounds of discussion (1-10)</li>
                    <li><strong>Start Debate:</strong> Click "Start Debate" and watch the conversation unfold!</li>
                </ol>
            </div>
            
            <div class="help-section">
                <h4>Understanding Modes</h4>
                <ul>
                    <li><strong>echo_er:</strong> Focus on positive aspects and opportunities</li>
                    <li><strong>invert_er:</strong> Challenge assumptions and point out contradictions</li>
                    <li><strong>what_if_er:</strong> Explore alternative scenarios and possibilities</li>
                    <li><strong>so_what_er:</strong> Question implications and demand practical impact</li>
                    <li><strong>cucumb_er:</strong> Stay analytical and provide systematic analysis</li>
                    <li><strong>archiv_er:</strong> Connect to history and provide contextual precedents</li>
                </ul>
            </div>
            
            <div class="help-section">
                <h4>Metrics & Progress</h4>
                <p>The right panel shows real-time analysis of your debate:</p>
                <ul>
                    <li><strong>Agreement Score:</strong> How much participants align (0-10)</li>
                    <li><strong>Convergence Status:</strong> Whether views are converging, diverging, or stable</li>
                    <li><strong>Emotional Sensitivity:</strong> Intensity of emotional language</li>
                    <li><strong>Bias Level:</strong> Detected bias in arguments (Low/Neutral/High)</li>
                    <li><strong>Topic Drift:</strong> How much discussion has strayed from the original topic</li>
                </ul>
                <div class="help-tips">
                    <strong>Tip:</strong> Metrics are calculated by an AI analyzer after each full turn, giving insight into debate dynamics!
                </div>
            </div>
            
            <div class="help-section">
                <h4>Interactive Features</h4>
                <ul>
                    <li><strong>Participate Yourself:</strong> Select <code>USER</code> in "One-to-one Debate" or "Panel Discussion" to participate as a debater or moderator. You'll be prompted to enter your response when it's your turn.</li>
                    <li><strong>Progressive Mode:</strong> Messages appear one at a time as they're generated for better engagement</li>
                    <li><strong>Theme Toggle:</strong> Switch between light and dark themes using the moon/sun button in the header</li>
                    <li><strong>Collapse Panels:</strong> Hide left or right sidebars for more focus on the debate transcript</li>
                </ul>
            </div>
            
            <div class="help-section">
                <h4>Technical Notes</h4>
                <ul>
                    <li>All debates are powered by local LLMs via Ollama (no cloud dependencies)</li>
                    <li>Metrics analysis uses <code>gemma3:27b</code> model at temperature 0.3</li>
                    <li>Context window supports up to 128,000 tokens for long debates</li>
                    <li>Starting a new debate clears all previous context automatically</li>
                </ul>
                <div class="help-tips">
                    <strong>Pro Tip:</strong> Mix different modes and tones to create dynamic, multi-perspective debates that explore all angles of a topic!
                </div>
            </div>
        </div>
    `;
    
    // Update topic header
    document.getElementById('current-topic').textContent = 'Help - How to Use TwistedDebate';
    
    showNotification('Help displayed. Start a new debate to continue.', 'info');
}

function showLicense() {
    const container = document.getElementById('transcript');
    container.innerHTML = `
        <div class="help-content">
            <h3>MIT License</h3>
            <div class="help-section" style="font-family: 'Courier New', monospace; white-space: pre-wrap; line-height: 1.6;">
MIT License

Copyright (c) 2026 Satoru Isaka

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
            </div>
            <div style="text-align: center; margin-top: 2rem;">
                <button id="return-to-help-btn" class="btn-secondary">← Return to Help</button>
            </div>
        </div>
    `;
    
    // Add event listener for return button
    document.getElementById('return-to-help-btn').addEventListener('click', showHelp);
    
    // Update topic header
    document.getElementById('current-topic').textContent = 'MIT License';
    
    showNotification('License displayed. Start a new debate to continue.', 'info');
}

function showNotification(message, type = 'info') {
    console.log(`[${type.toUpperCase()}] ${message}`);
    // TODO: Implement toast notification system
    if (type === 'error') {
        alert(message);
    }
}

// ================================
// Utilities
// ================================
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function addThinkingMessage(message) {
    const container = document.getElementById('transcript');
    
    // Remove welcome message if present
    const welcome = container.querySelector('.welcome-message');
    if (welcome) welcome.remove();
    
    const thinkingDiv = document.createElement('div');
    thinkingDiv.className = 'thinking-message';
    thinkingDiv.innerHTML = `
        <div class="loading-indicator">
            <span class="spinner"></span>
            <span>${message}</span>
        </div>
    `;
    
    container.appendChild(thinkingDiv);
    container.scrollTop = container.scrollHeight;
}

function clearThinkingMessages() {
    const container = document.getElementById('transcript');
    const thinkingMessages = container.querySelectorAll('.thinking-message');
    thinkingMessages.forEach(msg => msg.remove());
}

function updateGainDescription(gain) {
    const descriptions = {
        1: 'Minimal - Very conservative arguments',
        2: 'Low - Gentle perspective shifts',
        3: 'Low-Medium - Measured arguments',
        4: 'Medium-Low - Moderate intensity',
        5: 'Medium - Balanced debate intensity',
        6: 'Medium-High - Active engagement',
        7: 'High - Strong perspectives',
        8: 'High - Bold arguments',
        9: 'Very High - Highly creative',
        10: 'Maximum - Extremely exploratory'
    };
    
    const descEl = document.getElementById('gain-description');
    if (descEl) {
        descEl.textContent = descriptions[gain] || 'Medium - Balanced debate intensity';
    }
}

// ================================
// Export for debugging
// ================================
if (typeof window !== 'undefined') {
    window.TwistedDebateApp = {
        state: AppState,
        FormatConfigs,
        addMessage,
        updateProgress
    };
}
