import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';

document.addEventListener('DOMContentLoaded', () => {
    const projectList = document.getElementById('project-list');
    const codeEditor = document.getElementById('code-editor');
    
    // Initialize CodeMirror
    const editor = CodeMirror.fromTextArea(codeEditor, {
        mode: 'python',
        theme: 'monokai',
        lineNumbers: true,
        indentUnit: 4,
        smartIndent: true
    });
    
    const saveBtn = document.getElementById('save-btn');
    const runBtn = document.getElementById('run-btn');
    const consoleOutput = document.getElementById('console-output');
    const newProjectBtn = document.getElementById('new-project-btn');
    const modalOverlay = document.getElementById('modal-overlay');
    const createProjectBtn = document.getElementById('create-project-btn');
    const cancelProjectBtn = document.getElementById('cancel-project-btn');
    const newProjectNameInput = document.getElementById('new-project-name');

    // Help Modal Elements
    const helpBtn = document.getElementById('help-btn');
    const helpModalOverlay = document.getElementById('help-modal-overlay');
    const closeHelpBtn = document.getElementById('close-help-btn');

    // Debugger Elements
    const loadCircuitBtn = document.getElementById('load-circuit-btn');
    const resetDebugBtn = document.getElementById('reset-debug-btn');
    const stepDebugBtn = document.getElementById('step-debug-btn');
    const debugStatus = document.getElementById('debug-status');
    const debugCurrentStep = document.getElementById('debug-current-step');
    const debugTotalSteps = document.getElementById('debug-total-steps');
    const debugGateInfo = document.getElementById('debug-gate-info');
    const debugQubitProbs = document.getElementById('debug-qubit-probs');

    // Visual Builder Elements
    const visualBuilderToggle = document.getElementById('visual-builder-toggle');
    const visualBuilderContainer = document.getElementById('visual-builder-container');
    const circuitCanvas = document.getElementById('circuit-canvas');
    const gatePalette = document.getElementById('gate-palette');

    let currentProject = null;
    let currentFile = null;

    // --- Floating Window Logic ---
    const telemetryWindow = document.getElementById('telemetry-window');
    const debuggerWindow = document.getElementById('debugger-window');
    const photonicWindow = document.getElementById('photonic-window');
    const toggleTelemetryBtn = document.getElementById('toggle-telemetry-btn');
    const toggleDebuggerBtn = document.getElementById('toggle-debugger-btn');
    const togglePhotonicBtn = document.getElementById('toggle-photonic-btn');

    function toggleWindow(windowEl, btnEl) {
        if (windowEl.classList.contains('hidden')) {
            windowEl.classList.remove('hidden');
            btnEl.classList.add('active');
            // Bring to front
            windowEl.style.zIndex = getMaxZIndex() + 1;
        } else {
            windowEl.classList.add('hidden');
            btnEl.classList.remove('active');
        }
    }

    toggleTelemetryBtn.onclick = () => toggleWindow(telemetryWindow, toggleTelemetryBtn);
    toggleDebuggerBtn.onclick = () => toggleWindow(debuggerWindow, toggleDebuggerBtn);
    togglePhotonicBtn.onclick = () => toggleWindow(photonicWindow, togglePhotonicBtn);

    // Close buttons
    document.querySelectorAll('.close-window-btn').forEach(btn => {
        btn.onclick = () => {
            const targetId = btn.getAttribute('data-target');
            const targetWindow = document.getElementById(targetId);
            if (targetWindow) {
                targetWindow.classList.add('hidden');
                // Update toggle button state
                if (targetId === 'telemetry-window') toggleTelemetryBtn.classList.remove('active');
                if (targetId === 'debugger-window') toggleDebuggerBtn.classList.remove('active');
                if (targetId === 'photonic-window') togglePhotonicBtn.classList.remove('active');
            }
        };
    });

    // Make windows draggable
    function makeDraggable(el) {
        if (!el) return; // Guard clause
        const header = el.querySelector('.window-header');
        let isDragging = false;
        let startX, startY, initialLeft, initialTop;

        header.addEventListener('mousedown', (e) => {
            isDragging = true;
            startX = e.clientX;
            startY = e.clientY;
            
            const rect = el.getBoundingClientRect();
            
            // Lock current position as absolute left/top
            el.style.left = rect.left + 'px';
            el.style.top = rect.top + 'px';
            el.style.right = 'auto'; // Unset CSS right
            el.style.bottom = 'auto'; // Unset CSS bottom
            
            initialLeft = rect.left;
            initialTop = rect.top;

            // Bring to front
            // Use a simple high z-index or increment a global counter if needed
            // For now, just ensuring it's above other windows
            document.querySelectorAll('.floating-window').forEach(w => w.style.zIndex = 100);
            el.style.zIndex = 101;
            
            document.body.style.userSelect = 'none';
        });

        document.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            const dx = e.clientX - startX;
            const dy = e.clientY - startY;
            el.style.left = (initialLeft + dx) + 'px';
            el.style.top = (initialTop + dy) + 'px';
        });

        document.addEventListener('mouseup', () => {
            isDragging = false;
            document.body.style.userSelect = '';
        });
    }

    function getMaxZIndex() {
        // ... (unused now with simplified logic, but kept for compatibility if needed)
        return 100; 
    }

    makeDraggable(telemetryWindow);
    makeDraggable(debuggerWindow);
    makeDraggable(photonicWindow);

    // Initial State: Show Telemetry
    telemetryWindow.classList.remove('hidden');
    toggleTelemetryBtn.classList.add('active');

    // --- Chart.js Declarations ---
    const ctx = document.getElementById('sphyWaveChart').getContext('2d');
    let sphyChart; // Chart.js instance

    // --- Three.js Mimetic Electron Flow Visualization ---
    let renderer, scene, camera, points, controls;
    const particleRows = 50;
    const particleCols = 64; // Downsample wave to 64 points
    let waveBuffer = new Array(particleRows).fill(new Array(particleCols).fill(0));

    // --- Socket.IO Client Setup ---
    const socket = io(); // Connect to the WebSocket server

    socket.on('connect', () => {
        consoleOutput.textContent += '\nConnected to real-time telemetry stream via WebSocket.';
    });

    socket.on('telemetry_data', (data) => {
        updateTelemetry(data);
    });

    socket.on('status', (data) => {
        console.log('WebSocket Status:', data.message);
    });

    // --- Unified Telemetry Update Function ---
    function updateTelemetry(data) {
        console.log('Telemetry received:', data.waves.length, 'waves'); // Added log
        // Update Chart.js (2D Waveform)
        if (!sphyChart) { // Initialize if not already
            sphyChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [], // Will be populated with indices
                    datasets: [{
                        label: 'SPHY Wave Amplitude (12-bit)',
                        data: [],
                        borderColor: '#2ea043', // Green
                        backgroundColor: 'rgba(46, 160, 67, 0.1)',
                        borderWidth: 2,
                        pointRadius: 0,
                        tension: 0.4 // Smooth curve
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: { display: false, grid: { color: '#30363d' } },
                        y: { beginAtZero: true, max: 4095, grid: { color: '#30363d' }, ticks: { color: '#8b949e' } }
                    },
                    plugins: {
                        legend: {
                            labels: { color: '#c9d1d9', font: { family: "'Roboto Mono', monospace" } }
                        }
                    },
                    animation: { duration: 1000, easing: 'easeOutQuart' }
                }
            });
        }
        if (data.waves) {
            const labels = data.waves.map((_, index) => index);
            sphyChart.data.labels = labels;
            sphyChart.data.datasets[0].data = data.waves;
            sphyChart.update();
        }
        
        // Update LEDs
        if (data.leds) {
            data.leds.forEach((state, idx) => {
                const led = document.getElementById(`led-${idx}`);
                if (led) {
                    if (state) led.classList.add('on');
                    else led.classList.remove('on');
                }
            });
        }
        
        // Update Mode Badge
        const modeBadge = document.getElementById('mode-badge');
        if (modeBadge) { // Check if element exists
            if (data.is_hardware) {
                modeBadge.textContent = "HARDWARE";
                modeBadge.classList.add('hardware');
            } else {
                modeBadge.textContent = "SIMULATION";
                modeBadge.classList.remove('hardware');
            }
        }

        // Update 3D Visualization
        if (typeof updateThreeJS === 'function') {
            updateThreeJS(data.waves);
        }
    }

    function initThreeJS() {
        const container = document.getElementById('three-container');
        if (!container) return;

        const width = container.clientWidth;
        const height = container.clientHeight;

        // Scene
        scene = new THREE.Scene();
        scene.background = new THREE.Color(0x0d1117);
        scene.fog = new THREE.FogExp2(0x0d1117, 0.05);

        // Camera
        camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
        camera.position.set(0, 5, 10);
        camera.lookAt(0, 0, 0);

        // Renderer
        renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setSize(width, height);
        renderer.setPixelRatio(window.devicePixelRatio);
        container.appendChild(renderer.domElement);

        // OrbitControls
        controls = new OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;
        controls.screenSpacePanning = false;
        controls.minDistance = 5;
        controls.maxDistance = 50;
        controls.maxPolarAngle = Math.PI / 2;

        // Geometry (Particles)
        const geometry = new THREE.BufferGeometry();
        const positions = new Float32Array(particleRows * particleCols * 3);
        const colors = new Float32Array(particleRows * particleCols * 3);

        let idx = 0;
        for (let r = 0; r < particleRows; r++) {
            for (let c = 0; c < particleCols; c++) {
                const x = (c / particleCols - 0.5) * 20;
                const z = (r / particleRows - 0.5) * 30 - 5;
                
                positions[idx * 3] = x;
                positions[idx * 3 + 1] = 0;
                positions[idx * 3 + 2] = z;

                colors[idx * 3] = 0.2;
                colors[idx * 3 + 1] = 0.8;
                colors[idx * 3 + 2] = 0.4;

                idx++;
            }
        }

        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

        // Material
        const material = new THREE.PointsMaterial({
            size: 0.25,
            vertexColors: true,
            blending: THREE.AdditiveBlending,
            transparent: true,
            opacity: 0.8
        });

        points = new THREE.Points(geometry, material);
        scene.add(points);

        // Resize handler
        window.addEventListener('resize', () => {
            if (!container) return;
            const newWidth = container.clientWidth;
            const newHeight = container.clientHeight;
            camera.aspect = newWidth / newHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(newWidth, newHeight);
        });

        animate();
    }

    function updateThreeJS(newWave) {
        console.log('updateThreeJS called. newWave:', newWave ? newWave.length : 'null'); // Added log
        if (!points || !newWave) {
            console.warn('updateThreeJS: points or newWave is invalid. points:', points, 'newWave:', newWave); // Added log
            return;
        }

        const sampledWave = [];
        const step = Math.floor(newWave.length / particleCols);
        for (let i = 0; i < particleCols; i++) {
            sampledWave.push(newWave[i * step] || 0);
        }

        waveBuffer.pop();
        waveBuffer.unshift(sampledWave);

        const positions = points.geometry.attributes.position.array;
        const colors = points.geometry.attributes.color.array;

        let idx = 0;
        for (let r = 0; r < particleRows; r++) {
            const rowData = waveBuffer[r];
            for (let c = 0; c < particleCols; c++) {
                const amp = (rowData[c] || 0);
                const y = (amp / 4095) * 5; 

                positions[idx * 3 + 1] = y;

                const intensity = amp / 4095;
                colors[idx * 3] = 0.1;
                colors[idx * 3 + 1] = 0.5 + intensity * 0.5;
                colors[idx * 3 + 2] = 0.2 + intensity * 0.8;

                idx++;
            }
        }

        points.geometry.attributes.position.needsUpdate = true;
        points.geometry.attributes.color.needsUpdate = true;
    }

    function animate() {
        console.log('animate loop running...'); // Added log
        requestAnimationFrame(animate);
        
        if (controls) {
            controls.update();
        }
        
        if (renderer && scene && camera) {
            renderer.render(scene, camera);
        }
    }

    // --- Console Resizing Logic ---
    const resizer = document.getElementById('console-resizer');
    const consolePane = document.getElementById('console-pane');
    
    let isResizing = false;
    let lastDownY = 0;
    
    resizer.addEventListener('mousedown', (e) => {
        isResizing = true;
        lastDownY = e.clientY;
        document.body.style.cursor = 'ns-resize';
        document.body.style.userSelect = 'none'; // Prevent text selection
    });
    
    document.addEventListener('mousemove', (e) => {
        if (!isResizing) return;
        
        const deltaY = lastDownY - e.clientY;
        lastDownY = e.clientY;
        
        const currentHeight = consolePane.offsetHeight;
        const newHeight = currentHeight + deltaY;
        
        if (newHeight > 50) { // Min height
            consolePane.style.height = `${newHeight}px`;
        }
    });
    
    document.addEventListener('mouseup', () => {
        if (isResizing) {
            isResizing = false;
            document.body.style.cursor = 'default';
            document.body.style.userSelect = '';
            editor.refresh(); // Refresh CodeMirror after resize
        }
    });

    // --- Project Management ---

    function loadProjects() {
        fetch('/api/projects')
            .then(res => res.json())
            .then(data => {
                projectList.innerHTML = '';
                if (data.projects && data.projects.length > 0) {
                    data.projects.forEach(proj => {
                        const div = document.createElement('div');
                        div.className = 'project-item';
                        div.textContent = `[F] ${proj}`; // Changed from 📂 to [F]
                        div.onclick = () => loadProjectFiles(proj);
                        projectList.appendChild(div);
                    });
                } else {
                    projectList.innerHTML = '<div style="padding:10px; color:#8b949e">No projects found. Create one!</div>';
                }
            })
            .catch(err => console.error(err));
    }

    function loadProjectFiles(projectName) {
        currentProject = projectName;
        const file = 'main.py';
        
        document.querySelectorAll('.project-item').forEach(el => el.classList.remove('active'));
        loadFile(projectName, file);
    }

    function loadFile(project, filename) {
        fetch(`/api/files?project=${project}&filename=${filename}`)
            .then(res => res.json())
            .then(data => {
                if (data.content !== undefined) {
                    editor.setValue(data.content);
                    currentFile = filename;
                    document.getElementById('current-file').textContent = `${project}/${filename}`;
                    saveBtn.disabled = false;
                    runBtn.disabled = false;
                }
            })
            .catch(err => console.error(err));
    }

    // --- Editor Actions ---

    saveBtn.onclick = () => {
        if (!currentProject || !currentFile) return;
        
        const content = editor.getValue();
        fetch('/api/files', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                project: currentProject,
                filename: currentFile,
                content: content
            })
        })
        .then(res => res.json())
        .then(data => {
            consoleOutput.textContent += `
[Saved] ${currentProject}/${currentFile}`;
        });
    };

    runBtn.onclick = () => {
        const code = editor.getValue();
        consoleOutput.textContent = `> Compiling to SPHY Waves...\n`;
        
        fetch('/api/execute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code: code })
        })
        .then(res => res.json())
        .then(data => {
            if (data.output) {
                consoleOutput.textContent += data.output;
            } else if (data.error) {
                consoleOutput.textContent += `Error: ${data.error}`;
                if (data.traceback) {
                    consoleOutput.textContent += `
Traceback:
${data.traceback}`;
                }
            }
            consoleOutput.scrollTop = consoleOutput.scrollHeight;
        })
        .catch(err => {
            consoleOutput.textContent += `Network Error: ${err}`;
        });
    };

    // --- Modal Actions ---

    newProjectBtn.onclick = () => {
        modalOverlay.classList.remove('hidden');
        newProjectNameInput.focus();
    };

    cancelProjectBtn.onclick = () => {
        modalOverlay.classList.add('hidden');
        newProjectNameInput.value = '';
    };

    createProjectBtn.onclick = () => {
        const name = newProjectNameInput.value.trim();
        if (!name) return;

        fetch('/api/projects', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: name })
        })
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
            } else {
                modalOverlay.classList.add('hidden');
                newProjectNameInput.value = '';
                loadProjects(); // Refresh list
            }
        });
    };

    // --- AI Mode Logic ---
    const aiToggle = document.getElementById('ai-mode-toggle');
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const sidebar = document.querySelector('.sidebar');
    
    if (mobileMenuBtn) {
        mobileMenuBtn.onclick = () => {
            sidebar.classList.toggle('open');
            
            let existingOverlay = document.querySelector('.sidebar-overlay');
            
            if (sidebar.classList.contains('open')) {
                if (!existingOverlay) {
                    const overlay = document.createElement('div');
                    overlay.className = 'sidebar-overlay';
                    overlay.style.position = 'fixed';
                    overlay.style.top = '0';
                    overlay.style.left = '0';
                    overlay.style.width = '100vw';
                    overlay.style.height = '100vh';
                    overlay.style.backgroundColor = 'rgba(0,0,0,0.5)';
                    overlay.style.zIndex = '99';
                    document.body.appendChild(overlay);
                    
                    overlay.onclick = () => {
                        sidebar.classList.remove('open');
                        overlay.remove();
                    };
                }
            } else {
                 if (existingOverlay) existingOverlay.remove();
            }
        };
    }
    const aiPromptContainer = document.getElementById('ai-prompt-container');
    const aiPromptInput = document.getElementById('ai-prompt-input');
    const generateCodeBtn = document.getElementById('generate-code-btn');

    aiToggle.onchange = () => {
        if (aiToggle.checked) {
            aiPromptContainer.classList.remove('hidden');
            visualBuilderContainer.classList.add('hidden'); // Hide visual builder if AI is on
            visualBuilderToggle.checked = false;
            editor.getWrapperElement().classList.add('hidden'); // Hide CodeMirror
            aiPromptInput.focus();
        } else {
            aiPromptContainer.classList.add('hidden');
            editor.getWrapperElement().classList.remove('hidden'); // Show CodeMirror
        }
    };

    generateCodeBtn.onclick = () => {
        const prompt = aiPromptInput.value.trim();
        if (!prompt) return;

        generateCodeBtn.disabled = true;
        generateCodeBtn.textContent = "Qusq is thinking... ⏳";
        consoleOutput.textContent = `> Asking Qusq: "${prompt}"...
`;

        fetch('/api/ai/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                prompt: prompt,
                code: editor.getValue() 
            })
        })
        .then(res => res.json())
        .then(data => {
            if (data.code) {
                console.log("Qusq generated code:", data.code); // Debug log
                editor.setValue(data.code);
                consoleOutput.textContent += `> Qusq generated code successfully!
`;
                // Switch out of AI mode and show the editor
                aiToggle.checked = false;
                aiPromptContainer.classList.add('hidden');
                editor.getWrapperElement().classList.remove('hidden');
                editor.refresh();
            } else if (data.error) {
                consoleOutput.textContent += `Qusq Error: ${data.error}
`;
            }
        })
        .catch(err => {
            consoleOutput.textContent += `Network Error: ${err}
`;
        })
        .finally(() => {
            generateCodeBtn.disabled = false;
            generateCodeBtn.textContent = "Ask Qusq 🪄";
            consoleOutput.scrollTop = consoleOutput.scrollHeight;
        });
    };

    // --- Visual Builder Actions ---
    let currentVisualCircuit = []; // Stores gates in the visual builder
    let numQubits = 2; // Default number of qubits, can be made dynamic

    function renderVisualCircuit() {
        circuitCanvas.innerHTML = ''; // Clear existing
        const laneHeight = 40; 
        const gateWidth = 30;
        const gateSpacing = 20; // Space between gates in a moment

        // Draw horizontal grid lines for qubit lanes
        for (let i = 0; i < numQubits; i++) {
            const laneLine = document.createElement('div');
            laneLine.className = 'qubit-lane-line';
            laneLine.style.top = `${i * laneHeight + (laneHeight / 2) - 0.5}px`; // Centered line
            circuitCanvas.appendChild(laneLine);
        }

        // Draw qubit labels
        for (let i = 0; i < numQubits; i++) {
            const qubitLabelDiv = document.createElement('div');
            qubitLabelDiv.className = 'qubit-label';
            qubitLabelDiv.textContent = `q${i}`;
            qubitLabelDiv.style.top = `${i * laneHeight + (laneHeight / 2) - 10}px`; // Centered
            qubitLabelDiv.style.left = `5px`;
            circuitCanvas.appendChild(qubitLabelDiv);
        }

        // Sort gates by moment then by qubit index for consistent rendering
        currentVisualCircuit.sort((a, b) => a.momentIndex - b.momentIndex || a.qubitIndex - b.qubitIndex);

        const momentOffsets = {}; // To track X position for each moment
        currentVisualCircuit.forEach(gate => {
            const gateDiv = document.createElement('div');
            gateDiv.className = `dropped-gate ${gate.gateType.toLowerCase()}-gate`;
            gateDiv.textContent = gate.gateType;
            gateDiv.dataset.gateType = gate.gateType;
            gateDiv.dataset.qubitIndex = gate.qubitIndex;
            gateDiv.dataset.momentIndex = gate.momentIndex;
            if (gate.targetQubitIndex !== undefined) {
                gateDiv.dataset.targetQubitIndex = gate.targetQubitIndex;
            }

            // Calculate x position based on moment index
            if (!momentOffsets[gate.momentIndex]) {
                momentOffsets[gate.momentIndex] = 50; // Starting x for this moment, after qubit labels
            }
            let xPos = momentOffsets[gate.momentIndex];
            
            gateDiv.style.left = `${xPos}px`; 

            if (gate.gateType === 'CNOT') {
                const controlQubit = Math.min(gate.qubitIndex, gate.targetQubitIndex);
                const targetQubit = Math.max(gate.qubitIndex, gate.targetQubitIndex);
                const cnotHeight = (targetQubit - controlQubit) * laneHeight + laneHeight;
                
                gateDiv.style.top = `${controlQubit * laneHeight + (laneHeight - cnotHeight) / 2}px`;
                gateDiv.style.height = `${cnotHeight}px`;
                // For now, simple text, but could be drawn with SVG

                // Update x offset for next gate in this moment
                momentOffsets[gate.momentIndex] += gateWidth + gateSpacing;

            } else {
                gateDiv.style.top = `${gate.qubitIndex * laneHeight + (laneHeight - gateWidth) / 2}px`; // Centered in lane
                // Update x offset for next gate in this moment
                momentOffsets[gate.momentIndex] += gateWidth + gateSpacing;
            }
            circuitCanvas.appendChild(gateDiv);
        });
        editor.setValue(generateCirqCodeFromVisualCircuit());
    }

    // Function to generate Cirq code from the visual circuit
    function generateCirqCodeFromVisualCircuit() {
        if (currentVisualCircuit.length === 0) {
            return `import cirq\n\n# Define qubits\n${Array.from({length: numQubits}, (_, i) => `q${i} = cirq.NamedQubit("q${i}")`).join('\n')}\n\n# Create a circuit\ncircuit = cirq.Circuit()\n`;
        }

        let code = `import cirq\n`;
        code += `from qurq.ops import H, CNOT, Stabilize, X, Y, Z, I # Import mimetic ops\n\n`; 
        code += `# Define qubits\n`;
        code += `${Array.from({length: numQubits}, (_, i) => `q${i} = cirq.NamedQubit("q${i}")`).join('\n')}\n\n`;
        code += `# Create a circuit\ncircuit = cirq.Circuit(\n`;

        // Group gates by moment
        const moments = {};
        currentVisualCircuit.forEach(gate => {
            if (!moments[gate.momentIndex]) {
                moments[gate.momentIndex] = [];
            }
            moments[gate.momentIndex].push(gate);
        });

        Object.keys(moments).sort((a, b) => a - b).forEach(momentIndex => {
            code += `    cirq.Moment(\n`;
            // Sort gates within a moment by qubit index for consistent Cirq code
            moments[momentIndex].sort((a,b) => a.qubitIndex - b.qubitIndex).forEach(gate => {
                if (gate.gateType === 'CNOT') {
                    code += `        CNOT(q${gate.qubitIndex}, q${gate.targetQubitIndex}),\n`;
                } else if (gate.gateType === 'M') {
                    code += `        cirq.measure(q${gate.qubitIndex}),\n`;
                } else {
                    code += `        ${gate.gateType}(q${gate.qubitIndex}),\n`;
                }
            });
            code += `    ),\n`;
        });
        code += `)\n\n`;
        code += `print(circuit)\n`; 
        return code;
    }

    // --- Visual Builder Toggle Logic ---
    visualBuilderToggle.onchange = () => {
        if (visualBuilderToggle.checked) {
            visualBuilderContainer.classList.remove('hidden');
            editor.getWrapperElement().classList.add('hidden'); // Hide CodeMirror
            aiPromptContainer.classList.add('hidden'); // Hide AI if visual builder is on
            aiToggle.checked = false;
            renderVisualCircuit(); // Render initial empty circuit
        } else {
            visualBuilderContainer.classList.add('hidden');
            editor.getWrapperElement().classList.remove('hidden'); // Show CodeMirror
        }
    };
    
    // --- Gate Palette Drag Logic ---
    let draggedGateType = null;
    gatePalette.querySelectorAll('.draggable-gate').forEach(gateDiv => {
        gateDiv.addEventListener('dragstart', (e) => {
            draggedGateType = gateDiv.dataset.gateType;
            e.dataTransfer.setData('text/plain', draggedGateType);
            gateDiv.classList.add('dragging');
        });

        gateDiv.addEventListener('dragend', (e) => {
            gateDiv.classList.remove('dragging');
        });
    });

    // --- Circuit Canvas Drop Logic ---
    circuitCanvas.addEventListener('dragover', (e) => {
        e.preventDefault(); // Allow drop
        e.dataTransfer.dropEffect = 'move';
    });

    circuitCanvas.addEventListener('drop', (e) => {
        e.preventDefault();
        if (!draggedGateType) return;

        const rect = circuitCanvas.getBoundingClientRect();
        const dropY = e.clientY - rect.top;
        const dropX = e.clientX - rect.left;

        const laneHeight = 40; 
        const qubitIndex = Math.floor(dropY / laneHeight);
        const momentIndex = Math.floor((dropX - 50) / (gateWidth + gateSpacing)); // Adjust for dynamic gate width

        if (qubitIndex >= numQubits || qubitIndex < 0) {
            console.warn("Dropped outside valid qubit lanes.");
            draggedGateType = null;
            return;
        }

        let newGate = {
            gateType: draggedGateType,
            qubitIndex: qubitIndex,
            momentIndex: momentIndex > 0 ? momentIndex : 0
        };

        if (draggedGateType === 'CNOT') {
            let targetQubitInput = prompt(`Enter target qubit for CNOT (0 to ${numQubits - 1}, different from ${qubitIndex}):`);
            let targetQubit = parseInt(targetQubitInput);

            if (!isNaN(targetQubit) && targetQubit >= 0 && targetQubit < numQubits && targetQubit !== qubitIndex) {
                newGate.targetQubitIndex = targetQubit;
                currentVisualCircuit.push(newGate);
            } else {
                alert("Invalid target qubit for CNOT. Please try again.");
            }
        } else {
            currentVisualCircuit.push(newGate);
        }
        
        renderVisualCircuit();
        draggedGateType = null;
    });

    // --- Debugger Actions ---
    loadCircuitBtn.onclick = async () => {
        const code = editor.getValue();
        consoleOutput.textContent = `> Loading circuit for debugger...\n`;
        try {
            const response = await fetch('/api/debug/load', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code: code })
            });
            const data = await response.json();
            if (data.error) {
                consoleOutput.textContent += `Error loading circuit: ${data.error}
`;
                if (data.traceback) consoleOutput.textContent += `${data.traceback}
`;
            } else {
                consoleOutput.textContent += `> Circuit loaded for debugger.\n`;
                updateDebuggerUI(data);
            }
        } catch (err) {
            consoleOutput.textContent += `Network Error: ${err}
`;
        }
        consoleOutput.scrollTop = consoleOutput.scrollHeight;
    };

    resetDebugBtn.onclick = async () => {
        consoleOutput.textContent = `> Resetting debugger...\n`;
        try {
            const response = await fetch('/api/debug/reset', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const data = await response.json();
            if (data.error) {
                consoleOutput.textContent += `Error resetting debugger: ${data.error}
`;
                if (data.traceback) consoleOutput.textContent += `${data.traceback}
`;
            } else {
                consoleOutput.textContent += `> Debugger reset.\n`;
                updateDebuggerUI(data);
            }
        } catch (err) {
            consoleOutput.textContent += `Network Error: ${err}
`;
        }
        consoleOutput.scrollTop = consoleOutput.scrollHeight;
    };

    stepDebugBtn.onclick = async () => {
        consoleOutput.textContent = `> Stepping through circuit (Step ${debugCurrentStep.textContent})...
`;
        try {
            const response = await fetch('/api/debug/step', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const data = await response.json();
            if (data.error) {
                consoleOutput.textContent += `Error stepping: ${data.error}
`;
                if (data.traceback) consoleOutput.textContent += `${data.traceback}
`;
            } else {
                consoleOutput.textContent += `> Step executed. Next gate: ${data.current_gate_info}
`;
                updateDebuggerUI(data);
            }
        } catch (err) {
            consoleOutput.textContent += `Network Error: ${err}
`;
        } finally {
            // Measure frame rate impact - rudimentary for now
            // Update performance stats here
        }
    };
    
    // --- Help Modal Logic ---
    helpBtn.onclick = () => {
        helpModalOverlay.classList.remove('hidden');
    };

    closeHelpBtn.onclick = () => {
        helpModalOverlay.classList.add('hidden');
    };

    // Close modals on outside click
    window.onclick = (event) => {
        if (event.target === modalOverlay) {
            modalOverlay.classList.add('hidden');
        }
        if (event.target === helpModalOverlay) {
            helpModalOverlay.classList.add('hidden');
        }
    };

    // Keyboard Shortcuts
    document.addEventListener('keydown', (e) => {
        // Ctrl+S to Save
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault();
            saveBtn.click();
        }
        // Ctrl+Enter to Run
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            runBtn.click();
        }
    });

    // Initial Load
    loadProjects();
    initThreeJS(); // Initialize Three.js on DOM load

    // Debugger UI Update Function
    function updateDebuggerUI(debugInfo) {
        debugStatus.textContent = debugInfo.status;
        debugCurrentStep.textContent = debugInfo.current_step;
        debugTotalSteps.textContent = debugInfo.total_steps;
        debugGateInfo.textContent = debugInfo.current_gate_info;

        // Update qubit probabilities
        debugQubitProbs.innerHTML = '';
        for (const qubit in debugInfo.qubit_probabilities) {
            const probData = debugInfo.qubit_probabilities[qubit];
            const probDiv = document.createElement('div');
            probDiv.className = 'qubit-prob-item';
            probDiv.innerHTML = `<span>${qubit}</span>: |0>: ${probData["0"]}, |1>: ${probData["1"]}`;
            debugQubitProbs.appendChild(probDiv);
        }

        // Enable/disable debugger controls based on status
        stepDebugBtn.disabled = debugInfo.status === 'Finished' || debugInfo.status === 'No Circuit';
        resetDebugBtn.disabled = debugInfo.status === 'No Circuit';

        // Update SPHY waves in 3D (and 2D via updateTelemetry)
        if (debugInfo.sphy_waves) {
             // Fake a telemetry_data object to trigger the unified update
            updateTelemetry({
                waves: debugInfo.sphy_waves,
                leds: [0,0,0,0], // Debugger info doesn't provide LEDs, assume off for now or use app.py logic
                is_hardware: false // Debugger is simulator based
            });
        }
    }

    // Fetch initial debug info
    fetch('/api/debug/info')
        .then(res => res.json())
        .then(data => {
            if (!data.error) {
                updateDebuggerUI(data);
            }
        })
        .catch(err => console.error("Failed to fetch initial debug info:", err));
});