import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';

document.addEventListener('DOMContentLoaded', function() {
    const ctx = document.getElementById('sphyWaveChart').getContext('2d');
    const applyGateBtn = document.getElementById('apply-gate-btn');
    const gateSelect = document.getElementById('gate-select');
    const consoleOutput = document.getElementById('gate-result');

    // --- Socket.IO Client Setup ---
    const socket = io();

    socket.on('connect', () => {
        console.log('Connected to WebSocket telemetry stream.');
    });

    socket.on('telemetry_data', (data) => {
        updateTelemetry(data);
    });

    socket.on('status', (data) => {
        console.log('WebSocket Status:', data.message);
    });

    // Chart Configuration
    let sphyChart = new Chart(ctx, {
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
                x: {
                    display: false, // Hide x-axis labels for cleaner look
                    grid: {
                        color: '#30363d'
                    }
                },
                y: {
                    beginAtZero: true,
                    max: 4095, // 12-bit max
                    grid: {
                        color: '#30363d'
                    },
                    ticks: {
                        color: '#8b949e'
                    }
                }
            },
            plugins: {
                legend: {
                    labels: {
                        color: '#c9d1d9',
                        font: {
                            family: "'Roboto Mono', monospace"
                        }
                    }
                }
            },
            animation: {
                duration: 1000,
                easing: 'easeOutQuart'
            }
        }
    });

    // Update Telemetry with data received from WebSocket
    function updateTelemetry(data) {
        if (data.waves) {
            console.log('Main Page - Telemetry received:', data.waves.length, 'waves. First 5:', data.waves.slice(0, 5)); // Added log
            const labels = data.waves.map((_, index) => index);
            sphyChart.data.labels = labels;
            sphyChart.data.datasets[0].data = data.waves;
            sphyChart.update();
            
            // Update 3D Visualization
            if (typeof updateThreeJS === 'function') {
                updateThreeJS(data.waves);
            }
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
    }

    // No longer polling, data comes from WebSocket
    // setInterval(updateTelemetry, 500);
    // updateTelemetry();

    // Handle Gate Application
    applyGateBtn.addEventListener('click', function() {
        const selectedGate = gateSelect.value;
        
        consoleOutput.textContent += `
> Applying Gate: ${selectedGate}...`;
        consoleOutput.scrollTop = consoleOutput.scrollHeight;

        fetch('/api/translate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ gate: selectedGate }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                consoleOutput.textContent += `
ERROR: ${data.error}`;
            } else {
                consoleOutput.textContent += `
SUCCESS: Phase Shift Calculated: ${data.phase_shift.toFixed(4)} rad`;
                consoleOutput.textContent += `
> Injecting parameters to AXI Bus... [SIMULATED]`;
                
                // Simulate a visual "pulse" on the chart or status
                const indicator = document.getElementById('status-indicator');
                if (indicator) { // Check if element exists
                    indicator.style.backgroundColor = '#fff';
                    setTimeout(() => {
                        indicator.style.backgroundColor = '#2ea043';
                    }, 200);
                }
            }
            consoleOutput.scrollTop = consoleOutput.scrollHeight;
        })
        .catch(error => {
            consoleOutput.textContent += `
NETWORK ERROR: ${error}`;
        });
    });

    // --- Three.js Mimetic Electron Flow Visualization ---
    let renderer, scene, camera, points, controls; // Added controls
    let particlesData = [];
    const particleRows = 50;
    const particleCols = 64; // Downsample wave to 64 points
    let waveBuffer = new Array(particleRows).fill(new Array(particleCols).fill(0));

    function initThreeJS() {
        const container = document.getElementById('three-container');
        if (!container) return;

        const width = container.clientWidth;
        const height = container.clientHeight;

        // Scene
        scene = new THREE.Scene();
        scene.background = new THREE.Color(0x0d1117); // Dark background matching theme
        scene.fog = new THREE.FogExp2(0x0d1117, 0.05);

        // Camera
        camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
        camera.position.set(0, 12, 40); // Adjusted for centered view
        camera.lookAt(0, 0, 0);

        // Renderer
        renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setSize(width, height);
        renderer.setPixelRatio(window.devicePixelRatio);
        container.appendChild(renderer.domElement);

        // OrbitControls
        controls = new OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true; // An animation loop is required when damping is enabled
        controls.dampingFactor = 0.05;
        controls.screenSpacePanning = false;
        controls.minDistance = 5;
        controls.maxDistance = 60; // Increased max distance
        controls.maxPolarAngle = Math.PI / 2; // Limit vertical rotation

        // Geometry (Particles)
        const geometry = new THREE.BufferGeometry();
        const positions = new Float32Array(particleRows * particleCols * 3);
        const colors = new Float32Array(particleRows * particleCols * 3);

        // Initialize positions in a grid
        let idx = 0;
        for (let r = 0; r < particleRows; r++) {
            for (let c = 0; c < particleCols; c++) {
                // x: spread across width (-10 to 10)
                // y: initial 0
                // z: spread across depth (-20 to 20)
                const x = (c / particleCols - 0.5) * 20;
                const z = (r / particleRows - 0.5) * 40; // Centered depth
                
                positions[idx * 3] = x;
                positions[idx * 3 + 1] = 0;
                positions[idx * 3 + 2] = z;

                // Initial color (greenish)
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
        if (!points || !newWave) return;

        // Downsample newWave to particleCols
        const sampledWave = [];
        const step = Math.floor(newWave.length / particleCols);
        for (let i = 0; i < particleCols; i++) {
            sampledWave.push(newWave[i * step] || 0);
        }

        // Update Buffer: Shift rows back
        waveBuffer.pop(); // Remove oldest (visually closest or furthest depending on flow)
        waveBuffer.unshift(sampledWave); // Add new to front

        // Update Geometry Positions
        const positions = points.geometry.attributes.position.array;
        const colors = points.geometry.attributes.color.array;

        let idx = 0;
        for (let r = 0; r < particleRows; r++) {
            const rowData = waveBuffer[r];
            for (let c = 0; c < particleCols; c++) {
                // Map amplitude (0-4095) to Y height (0-10) - Increased Y scaling
                const amp = (rowData[c] || 0);
                const y = (amp / 4095) * 10; 

                // Update Y position
                positions[idx * 3 + 1] = y;

                // Update Color based on height (Low: Green, High: White/Cyan)
                const intensity = amp / 4095;
                colors[idx * 3] = 0.1; // R
                colors[idx * 3 + 1] = 0.5 + intensity * 0.5; // G (0.5 to 1.0)
                colors[idx * 3 + 2] = 0.2 + intensity * 0.8; // B (0.2 to 1.0)

                idx++;
            }
        }

        points.geometry.attributes.position.needsUpdate = true;
        points.geometry.attributes.color.needsUpdate = true;
    }

    function animate() {
        requestAnimationFrame(animate);
        
        if (controls) { // Ensure controls are initialized
            controls.update(); // only required if controls.enableDamping is set to true
        }
        
        if (points) {
            // Subtle rotation for dynamic effect
            points.rotation.y += 0.001;
        }

        if (renderer && scene && camera) {
            renderer.render(scene, camera);
        }
    }

    // Initialize Three.js
    initThreeJS();
});
