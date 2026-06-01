// Project Benjamin SRE Dashboard Interactive Controller

document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const btnTrigger = document.getElementById("btn-trigger");
    const incidentList = document.getElementById("incident-list");
    const activeStatusBadge = document.getElementById("active-status-badge");
    const activeIncidentTitle = document.getElementById("active-incident-title");
    const activeIncidentMeta = document.getElementById("active-incident-meta");
    
    const timelineContainer = document.getElementById("timeline-container");
    const metricsSvg = document.getElementById("metrics-svg");
    const logsTerminal = document.getElementById("logs-terminal");
    
    // Safety Gate Elements
    const safetyGateCard = document.getElementById("safety-gate-card");
    const safetyRiskBadge = document.getElementById("safety-risk-badge");
    const proposedCommandText = document.getElementById("proposed-command-text");
    const safetyStatusText = document.getElementById("safety-status-text");
    const safetyReasonsText = document.getElementById("safety-reasons-text");
    
    // Comms Elements
    const commsFeedContainer = document.getElementById("comms-feed-container");
    
    // Active Leads Elements
    const leadCommander = document.getElementById("lead-commander");
    const leadOps = document.getElementById("lead-ops");
    const leadLogistics = document.getElementById("lead-logistics");
    const leadPlanning = document.getElementById("lead-planning");
    const leadComms = document.getElementById("lead-comms");
    
    // HITL Elements
    const btnApprove = document.getElementById("btn-approve-mutation");
    const btnReject = document.getElementById("btn-reject-mutation");
    const hitlActionsContainer = document.getElementById("hitl-actions-container");
    const projectIdInput = document.getElementById("project-id-input");
    
    // Discovery Elements
    const btnDiscoverProject = document.getElementById("btn-discover-project");
    const discoveredResourcesSection = document.getElementById("discovered-resources-section");
    const discoveredResourcesList = document.getElementById("discovered-resources-list");
    const discoveryVulnerabilityBadge = document.getElementById("discovery-vulnerability-badge");
    
    // Chat DOM Elements
    const chatMessagesContainer = document.getElementById("chat-messages-container");
    const chatUserInput = document.getElementById("chat-user-input");
    const btnChatSend = document.getElementById("btn-chat-send");
    
    let activeIncidentId = null;
    
    // Initialize
    loadConfig();
    loadIncidentRepository();
    
    // Event Listeners
    btnTrigger.addEventListener("click", triggerLiveSimulation);
    if (btnApprove) btnApprove.addEventListener("click", approveMutation);
    if (btnReject) btnReject.addEventListener("click", rejectMutation);
    if (btnChatSend) btnChatSend.addEventListener("click", sendChatMessage);
    if (btnDiscoverProject) btnDiscoverProject.addEventListener("click", handleProjectDiscovery);
    
    const projectLabel = document.querySelector('label[for="project-id-input"]');
    if (projectLabel) {
        projectLabel.style.cursor = "pointer";
        projectLabel.addEventListener("click", handleProjectDiscovery);
    }
    
    if (projectIdInput) {
        projectIdInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                handleProjectDiscovery();
            }
        });
    }
    
    if (chatUserInput) {
        chatUserInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                sendChatMessage();
            }
        });
    }
    
    // 0. Fetch Server Configurations
    async function loadConfig() {
        try {
            const res = await fetch("/api/config");
            const data = await res.json();
            if (data && data.project_id && projectIdInput) {
                projectIdInput.value = data.project_id;
                projectIdInput.placeholder = data.project_id;
                
                // Automatically trigger resource discovery on load
                handleProjectDiscovery();
            }
        } catch (err) {
            console.error("Failed to load server configurations:", err);
        }
    }

    // Approve proposed mutation via Safety Gate
    async function approveMutation() {
        if (!activeIncidentId) return;
        if (btnApprove) btnApprove.disabled = true;
        if (btnReject) btnReject.disabled = true;
        try {
            const res = await fetch(`/api/incidents/${activeIncidentId}/approve`, {
                method: "POST"
            });
            const data = await res.json();
            await loadIncidentRepository(activeIncidentId);
        } catch (err) {
            console.error("Failed to approve mutation:", err);
            alert("Error approving mutation.");
        } finally {
            if (btnApprove) btnApprove.disabled = false;
            if (btnReject) btnReject.disabled = false;
        }
    }

    // Reject and abort proposed mutation
    async function rejectMutation() {
        if (!activeIncidentId) return;
        if (btnApprove) btnApprove.disabled = true;
        if (btnReject) btnReject.disabled = true;
        try {
            const res = await fetch(`/api/incidents/${activeIncidentId}/reject`, {
                method: "POST"
            });
            const data = await res.json();
            await loadIncidentRepository(activeIncidentId);
        } catch (err) {
            console.error("Failed to reject mutation:", err);
            alert("Error rejecting mutation.");
        } finally {
            if (btnApprove) btnApprove.disabled = false;
            if (btnReject) btnReject.disabled = false;
        }
    }

    // Fetch and render contextual chat log
    async function loadChatMessages(incidentId) {
        if (!chatMessagesContainer) return;
        try {
            const res = await fetch(`/api/incidents/${incidentId}/chat`);
            const chatData = await res.json();
            
            if (!chatData || chatData.length === 0) {
                chatMessagesContainer.innerHTML = `<div class="chat-placeholder">Welcome! Write a message to initialize chat.</div>`;
                return;
            }
            
            chatMessagesContainer.innerHTML = "";
            chatData.forEach(msg => {
                const bubble = document.createElement("div");
                const isUser = msg.sender.includes("Operator");
                bubble.className = `chat-bubble ${isUser ? 'chat-bubble-user' : 'chat-bubble-agent'}`;
                
                const tDate = new Date(msg.timestamp);
                const timeStr = isNaN(tDate.getTime()) ? "" : tDate.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
                
                bubble.innerHTML = `
                    <div class="chat-meta ${isUser ? 'chat-meta-user' : 'chat-meta-agent'}">
                        <span>${msg.sender}</span>
                        <span>${timeStr}</span>
                    </div>
                    <div class="chat-text">${msg.message}</div>
                `;
                chatMessagesContainer.appendChild(bubble);
            });
            
            // Scroll to the bottom of message feeds
            chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
        } catch (err) {
            console.error("Failed to load chat history:", err);
            chatMessagesContainer.innerHTML = `<div class="chat-placeholder text-danger">Error loading chat interface.</div>`;
        }
    }

    // Send a message from the operator to SRE AI Incident Commander
    async function sendChatMessage() {
        if (!activeIncidentId || !chatUserInput) return;
        const msgText = chatUserInput.value.trim();
        if (!msgText) return;
        
        chatUserInput.value = "";
        if (btnChatSend) btnChatSend.disabled = true;
        
        try {
            const res = await fetch(`/api/incidents/${activeIncidentId}/chat`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: msgText })
            });
            const chatData = await res.json();
            
            // Re-render bubbles
            loadChatMessages(activeIncidentId);
        } catch (err) {
            console.error("Failed to post message:", err);
            alert("Failed to communicate with UI SRE Agent.");
        } finally {
            if (btnChatSend) btnChatSend.disabled = false;
        }
    }
    
    // 1. Fetch SRE Incident List
    async function loadIncidentRepository(selectedId = null) {
        try {
            const res = await fetch("/api/incidents");
            const incidents = await res.json();
            
            if (incidents.length === 0) {
                incidentList.innerHTML = `<li class="loading-placeholder">No incidents recorded yet.</li>`;
                return;
            }
            
            incidentList.innerHTML = "";
            incidents.forEach((inc, index) => {
                const li = document.createElement("li");
                li.className = `incident-item ${selectedId === inc.incident_id || (!selectedId && index === 0) ? 'active' : ''}`;
                li.dataset.id = inc.incident_id;
                
                const badgeClass = inc.status.toUpperCase() === "CLOSED" || inc.status.toUpperCase() === "RESOLVED" 
                    ? "status-resolved" 
                    : "status-active";
                    
                li.innerHTML = `
                    <div class="incident-item-header">
                        <span class="incident-item-id">${inc.incident_id}</span>
                        <span class="incident-item-status status-badge ${badgeClass}">${inc.status}</span>
                    </div>
                    <div class="incident-item-desc">${inc.trigger_event || 'SRE incident trigger'}</div>
                `;
                
                li.addEventListener("click", () => {
                    document.querySelectorAll(".incident-item").forEach(item => item.classList.remove("active"));
                    li.classList.add("active");
                    fetchIncidentDetails(inc.incident_id);
                });
                
                incidentList.appendChild(li);
            });
            
            // Auto-load details for selected or first incident
            if (selectedId) {
                fetchIncidentDetails(selectedId);
            } else if (incidents.length > 0) {
                fetchIncidentDetails(incidents[0].incident_id);
            }
        } catch (err) {
            console.error("Failed to load incident repository:", err);
            incidentList.innerHTML = `<li class="loading-placeholder text-danger">Error loading repository.</li>`;
        }
    }
    
    // 2. Fetch Single Incident Details
    async function fetchIncidentDetails(id) {
        activeIncidentId = id;
        try {
            const res = await fetch(`/api/incidents/${id}`);
            const data = await res.json();
            renderIncident(data);
        } catch (err) {
            console.error("Failed to fetch incident details:", err);
        }
    }
    
    // 3. Render Incident Info on Dashboard
    function renderIncident(inc) {
        // Update Title & Metadata
        activeIncidentTitle.textContent = inc.incident_id;
        activeIncidentMeta.innerHTML = `Target Project: <strong>${inc.project_id}</strong> | Trigger Event: <strong>${inc.trigger_event}</strong>`;
        
        // Status Badge
        const status = inc.status.toUpperCase();
        activeStatusBadge.textContent = status;
        activeStatusBadge.className = "status-badge " + (status === "RESOLVED" || status === "CLOSED" ? "status-resolved" : "status-active");
        
        // Handle Active Leads Badge highlights
        updateLeadsHighlight(inc.timeline);
        
        // Render Scribe Timeline with animated sequential delay
        renderTimeline(inc.timeline);
        
        // Render Diagnostics (Metrics + Logs)
        renderMetrics(inc.artifacts);
        renderLogs(inc.artifacts);
        
        // Render Safety Gate Evaluation
        renderSafetyGate(inc.timeline, status);
        
        // Render Comms Feeds
        renderComms(inc.artifacts);

        // Load Contextual Chat
        loadChatMessages(inc.incident_id);

        // Show/hide HITL buttons based on status
        if (hitlActionsContainer) {
            if (status === "AWAITING_APPROVAL") {
                hitlActionsContainer.style.display = "flex";
            } else {
                hitlActionsContainer.style.display = "none";
            }
        }
    }
    
    // Highlight which SRE leads participated in the incident timeline
    function updateLeadsHighlight(timeline) {
        const agents = new Set(timeline.map(e => e.agent.toLowerCase()));
        
        leadCommander.classList.toggle("active", agents.has("incident commander benjamin") || agents.has("benjamin"));
        leadOps.classList.toggle("active", agents.has("operations lead") || agents.has("ops lead"));
        leadLogistics.classList.toggle("active", agents.has("logistics lead"));
        leadPlanning.classList.toggle("active", agents.has("planning lead"));
        leadComms.classList.toggle("active", agents.has("communications lead") || [...agents].some(a => a.includes("communications lead")));
    }
    
    // Render Scribe chronological timeline log
    function renderTimeline(timeline) {
        if (!timeline || timeline.length === 0) {
            timelineContainer.innerHTML = `<div class="timeline-empty">No Scribe timeline events logged.</div>`;
            return;
        }
        
        timelineContainer.innerHTML = "";
        timeline.forEach((event, idx) => {
            const item = document.createElement("div");
            item.className = "timeline-event";
            item.style.animationDelay = `${idx * 0.1}s`;
            
            // Format timestamp nicely
            const tDate = new Date(event.timestamp);
            const timeStr = isNaN(tDate.getTime()) ? event.timestamp : tDate.toLocaleTimeString();
            
            item.innerHTML = `
                <div class="timeline-dot active"></div>
                <div class="timeline-event-header">
                    <span class="timeline-time">${timeStr}</span>
                    <span class="timeline-agent">${event.agent}</span>
                </div>
                <p class="timeline-message">${event.message}</p>
            `;
            timelineContainer.appendChild(item);
        });
    }
    
    // Parse metrics.csv and draw beautiful SVG lines
    function renderMetrics(artifacts) {
        const metricsArt = artifacts.find(a => a.file_path.endsWith("metrics.csv"));
        if (!metricsArt || !metricsArt.content) {
            metricsSvg.innerHTML = `<text x="250" y="100" text-anchor="middle" fill="#8b949e" font-size="12">No telemetry metrics available</text>`;
            return;
        }
        
        try {
            const lines = metricsArt.content.trim().split("\n");
            const headers = lines[0].split(",");
            const latencyData = [];
            const cpuData = [];
            
            // Parse CSV lines
            for (let i = 1; i < lines.length; i++) {
                const cols = lines[i].split(",");
                if (cols.length < 2) continue;
                const name = cols[0].trim();
                const value = parseFloat(cols[1]);
                if (name === "frontend_latency") {
                    latencyData.push(value);
                } else if (name === "cpu_utilization") {
                    cpuData.push(value);
                }
            }
            
            // Helper to generate SVG polyline points string scaled to fit
            const getPointsStr = (data, minVal, maxVal, color) => {
                const width = 450;
                const height = 150;
                const xOffset = 25;
                const yOffset = 25;
                
                const points = [];
                const step = width / (data.length - 1);
                const valRange = maxVal - minVal || 1;
                
                data.forEach((val, i) => {
                    const x = xOffset + (i * step);
                    // Invert y because SVG y goes down
                    const y = yOffset + height - ((val - minVal) / valRange * height);
                    points.push(`${x},${y}`);
                });
                return points.join(" ");
            };
            
            // Set scale min/max
            const maxLatency = Math.max(...latencyData, 100);
            const maxCpu = Math.max(...cpuData, 100);
            
            const latencyPoints = getPointsStr(latencyData, 0, maxLatency);
            const cpuPoints = getPointsStr(cpuData, 0, maxCpu);
            
            metricsSvg.innerHTML = `
                <!-- Grid Lines -->
                <line x1="25" y1="25" x2="475" y2="25" stroke="#21262d" stroke-dasharray="3,3" />
                <line x1="25" y1="100" x2="475" y2="100" stroke="#21262d" stroke-dasharray="3,3" />
                <line x1="25" y1="175" x2="475" y2="175" stroke="#30363d" />
                
                <!-- SVG Y Axes Labels -->
                <text x="5" y="30" fill="#ff3131" font-size="8" font-family="monospace">${Math.round(maxLatency)}ms</text>
                <text x="5" y="175" fill="#8b949e" font-size="8" font-family="monospace">0ms</text>
                
                <text x="480" y="30" fill="#00ffff" font-size="8" font-family="monospace">${Math.round(maxCpu)}%</text>
                
                <!-- Telemetry Lines -->
                <polyline fill="none" stroke="#ff3131" stroke-width="2.5" points="${latencyPoints}" />
                <polyline fill="none" stroke="#00ffff" stroke-width="2.5" points="${cpuPoints}" />
                
                <!-- Telemetry Data Dots -->
                ${latencyData.map((val, idx) => {
                    const pt = latencyPoints.split(" ")[idx].split(",");
                    return `<circle cx="${pt[0]}" cy="${pt[1]}" r="4" fill="#ff3131" stroke="#0d1117" stroke-width="1.5"/>`;
                }).join("")}
                
                ${cpuData.map((val, idx) => {
                    const pt = cpuPoints.split(" ")[idx].split(",");
                    return `<circle cx="${pt[0]}" cy="${pt[1]}" r="4" fill="#00ffff" stroke="#0d1117" stroke-width="1.5"/>`;
                }).join("")}
            `;
        } catch (e) {
            console.error("Failed to render metrics CSV:", e);
            metricsSvg.innerHTML = `<text x="250" y="100" text-anchor="middle" fill="#ff3131" font-size="12">Telemetry parsing error</text>`;
        }
    }
    
    // Highlight MySQL keywords inside logs terminal
    function renderLogs(artifacts) {
        const logArt = artifacts.find(a => a.file_path.endsWith(".log") || a.file_path.endsWith(".txt"));
        if (!logArt || !logArt.content) {
            logsTerminal.innerHTML = `<code>[No query log streams generated]</code>`;
            return;
        }
        
        let logText = logArt.content;
        
        // Dynamic Syntax Highlighting
        logText = logText
            .replace(/(SELECT|INSERT|UPDATE|DELETE|FROM|WHERE|JOIN|LIMIT)/gi, '<span style="color: #ff79c6; font-weight: bold;">$1</span>')
            .replace(/(ERROR|FAIL|CRITICAL)/gi, '<span style="color: #ff5555; font-weight: bold;">$1</span>')
            .replace(/(deadlock|lock contention|lock)/gi, '<span style="color: #ffb86c; font-weight: bold;">$1</span>')
            .replace(/(SUCCESS|OK|VERIFIED)/gi, '<span style="color: #50fa7b; font-weight: bold;">$1</span>');
            
        logsTerminal.innerHTML = `<code>${logText}</code>`;
        logsTerminal.scrollTop = logsTerminal.scrollHeight; // Auto-scroll to bottom
    }
    
    // Render risk and safety commands evaluated by Logistics Lead
    function renderSafetyGate(timeline, status) {
        const logiEvents = timeline.filter(e => e.agent.toLowerCase() === "logistics lead");
        if (logiEvents.length === 0) {
            proposedCommandText.textContent = "N/A";
            safetyStatusText.textContent = "AWAITING TRIAGE";
            safetyStatusText.className = "metric-value text-secondary";
            safetyReasonsText.textContent = "No mutation actions proposed by Operations Lead yet.";
            safetyRiskBadge.textContent = "PENDING";
            safetyRiskBadge.className = "risk-badge badge-low";
            return;
        }
        
        // Extract command details from timeline strings
        const riskEvent = logiEvents.find(e => e.message.includes("risk level") || e.message.includes("Risk level"));
        const commandEvent = timeline.find(e => e.agent.toLowerCase() === "operations lead" && e.message.includes("Proposed system mutation"));
        
        let cmd = "systemctl restart mysql";
        if (commandEvent) {
            const cmdMatch = commandEvent.message.match(/command:\s*(.*)/);
            if (cmdMatch) {
                cmd = cmdMatch[1].trim();
            } else if (commandEvent.message.includes("command: ")) {
                cmd = commandEvent.message.split("command: ")[1].trim();
            }
        }
        
        proposedCommandText.textContent = cmd;
        
        if (riskEvent) {
            const riskMatch = riskEvent.message.match(/level:\s*([A-Za-z]+)/i);
            const riskLevel = riskMatch ? riskMatch[1].toUpperCase() : "MEDIUM";
            
            safetyRiskBadge.textContent = riskLevel + " RISK";
            if (riskLevel === "HIGH") {
                safetyRiskBadge.className = "risk-badge badge-high";
            } else if (riskLevel === "MEDIUM") {
                safetyRiskBadge.className = "risk-badge badge-med";
            } else {
                safetyRiskBadge.className = "risk-badge badge-low";
            }
        }

        // Override status rendering based on manual approval gate state
        const upperStatus = status ? status.toUpperCase() : "UNKNOWN";
        if (upperStatus === "AWAITING_APPROVAL") {
            safetyStatusText.textContent = "AWAITING CLEARANCE";
            safetyStatusText.className = "metric-value text-warning";
            safetyReasonsText.textContent = "Proposed mutation command is held. Awaiting human operator safety clearance on the dashboard.";
        } else if (upperStatus === "ABORTED") {
            safetyStatusText.textContent = "REJECTED";
            safetyStatusText.className = "metric-value text-danger";
            safetyReasonsText.textContent = "Mutation command rejected and halted by manual safety override.";
        } else if (upperStatus === "CLOSED" || upperStatus === "RESOLVED") {
            safetyStatusText.textContent = "EXECUTED";
            safetyStatusText.className = "metric-value text-success";
            safetyReasonsText.textContent = "Mutation command approved and executed successfully.";
        } else {
            safetyStatusText.textContent = "APPROVED";
            safetyStatusText.className = "metric-value text-success";
            if (riskEvent) {
                safetyReasonsText.textContent = riskEvent.message;
            }
        }
    }
    
    // Render Madhavi's broadcast cards & GitHub Issue tickets
    function renderComms(artifacts) {
        const telegramArt = artifacts.find(a => a.file_path.endsWith("telegram_feed.json"));
        const githubArt = artifacts.find(a => a.file_path.endsWith("github_issue.json"));
        
        if (!telegramArt && !githubArt) {
            commsFeedContainer.innerHTML = `
                <div class="comms-card telegram">
                    <div class="comms-card-header">
                        <span class="channel-badge">Communications Offline</span>
                        <span class="comms-time">Offline</span>
                    </div>
                    <p class="comms-message">No active integration dispatches captured.</p>
                </div>
            `;
            return;
        }
        
        commsFeedContainer.innerHTML = "";
        
        // 1. Render GitHub Issue Card if available
        if (githubArt && githubArt.content) {
            try {
                const issue = JSON.parse(githubArt.content);
                const issueCard = document.createElement("div");
                issueCard.className = "comms-card github-issue-card";
                issueCard.style.borderLeft = "4px solid #58a6ff";
                issueCard.style.background = "rgba(88, 166, 255, 0.03)";
                issueCard.style.marginTop = "10px";
                
                const statusBadgeClass = issue.status === "open" ? "badge-low" : "badge-high";
                const statusText = issue.status.toUpperCase();
                
                let commentsHtml = "";
                if (issue.comments && issue.comments.length > 0) {
                    commentsHtml = `
                        <div class="github-comments-section" style="margin-top: 10px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.06);">
                            <span style="font-size: 10px; font-weight: 800; color: #8b949e;">COMMENTS (${issue.comments.length})</span>
                            <div class="github-comments-list" style="max-height: 120px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; margin-top: 6px;">
                                ${issue.comments.map(c => `
                                    <div class="github-comment" style="font-size: 11px; background: rgba(0,0,0,0.15); padding: 6px 8px; border-radius: 6px;">
                                        <strong>${c.author}:</strong> ${c.body}
                                    </div>
                                `).join("")}
                            </div>
                        </div>
                    `;
                }
                
                issueCard.innerHTML = `
                    <div class="comms-card-header">
                        <span class="channel-badge" style="color: #58a6ff;">🐙 GitHub Issue Ticket</span>
                        <span class="risk-badge ${statusBadgeClass}">${statusText}</span>
                    </div>
                    <h4 style="font-size: 13px; font-weight: 800; margin: 6px 0; color: #58a6ff;">${issue.title}</h4>
                    <p class="comms-message" style="font-size: 11.5px; color: #8b949e;">${issue.body}</p>
                    ${commentsHtml}
                `;
                commsFeedContainer.appendChild(issueCard);
            } catch (e) {
                console.error("Failed to parse github issue JSON:", e);
            }
        }
        
        // 2. Render Telegram dispatches if available
        if (telegramArt && telegramArt.content) {
            try {
                const feed = JSON.parse(telegramArt.content);
                feed.forEach((alert, idx) => {
                    const card = document.createElement("div");
                    card.className = "comms-card telegram";
                    card.style.borderLeft = "4px solid #00ffff";
                    card.style.background = "rgba(0, 255, 255, 0.02)";
                    card.style.marginTop = "10px";
                    
                    const tDate = new Date(alert.timestamp);
                    const timeStr = isNaN(tDate.getTime()) ? alert.timestamp : tDate.toLocaleTimeString();
                    
                    card.innerHTML = `
                        <div class="comms-card-header">
                            <span class="channel-badge" style="color: #00ffff;">📢 Telegram Broadcast</span>
                            <span class="comms-time">${timeStr}</span>
                        </div>
                        <p class="comms-message" style="font-size: 12px;">${alert.message}</p>
                    `;
                    commsFeedContainer.appendChild(card);
                });
            } catch (e) {
                console.error("Failed to parse telegram feed JSON:", e);
            }
        }
    }
    
    // 4. Trigger Live SRE Incident Simulation
    async function triggerLiveSimulation() {
        btnTrigger.disabled = true;
        btnTrigger.textContent = "Simulating Live Incident...";
        btnTrigger.classList.remove("animate-pulse");
        
        const projectIdVal = projectIdInput ? projectIdInput.value.trim() : "";
        const payload = {
            event_type: "frontend_latency_slo_violated"
        };
        if (projectIdVal) {
            payload.project_id = projectIdVal;
        }
        
        try {
            const res = await fetch("/api/simulate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            
            // Reload sidebar list and automatically select the new incident
            await loadIncidentRepository(data.incident_id);
            
            // Animate details appearing step-by-step
            animateIncidentArrival(data);
        } catch (err) {
            console.error("Failed to trigger simulation:", err);
            alert("Error running simulation on SRE Agent backend.");
        } finally {
            btnTrigger.disabled = false;
            btnTrigger.textContent = "Trigger Live Simulation";
            btnTrigger.classList.add("animate-pulse");
        }
    }
    
    // Beautiful sequential visualization animation for fresh incidents
    function animateIncidentArrival(inc) {
        // Render base details first
        activeIncidentTitle.textContent = inc.incident_id;
        activeIncidentMeta.innerHTML = `Target Project: <strong>${inc.project_id}</strong> | Trigger Event: <strong>${inc.trigger_event}</strong>`;
        
        // Hide logs & metrics initially
        metricsSvg.innerHTML = `<text x="250" y="100" text-anchor="middle" fill="#8b949e" font-size="12">Collecting telemetry diagnostics...</text>`;
        logsTerminal.innerHTML = `<code>[Initial audit. Scraping MySQL logs...]</code>`;
        
        // Progressively add timeline entries one by one to simulate live execution
        timelineContainer.innerHTML = "";
        let step = 0;
        
        const interval = setInterval(() => {
            if (step >= inc.timeline.length) {
                clearInterval(interval);
                // Finally populate metrics and logs
                renderMetrics(inc.artifacts);
                renderLogs(inc.artifacts);
                renderSafetyGate(inc.timeline, inc.status.toUpperCase());
                renderComms(inc.artifacts);
                
                const status = inc.status.toUpperCase();
                activeStatusBadge.textContent = status;
                activeStatusBadge.className = "status-badge " + (status === "RESOLVED" || status === "CLOSED" ? "status-resolved" : "status-active");
                
                // Show/hide HITL buttons based on status
                if (hitlActionsContainer) {
                    if (status === "AWAITING_APPROVAL") {
                        hitlActionsContainer.style.display = "flex";
                    } else {
                        hitlActionsContainer.style.display = "none";
                    }
                }
                return;
            }
            
            const event = inc.timeline[step];
            const item = document.createElement("div");
            item.className = "timeline-event";
            
            const tDate = new Date(event.timestamp);
            const timeStr = isNaN(tDate.getTime()) ? event.timestamp : tDate.toLocaleTimeString();
            
            item.innerHTML = `
                <div class="timeline-dot active"></div>
                <div class="timeline-event-header">
                    <span class="timeline-time">${timeStr}</span>
                    <span class="timeline-agent">${event.agent}</span>
                </div>
                <p class="timeline-message">${event.message}</p>
            `;
            timelineContainer.appendChild(item);
            
            // Incremental agent highlights
            updateLeadsHighlight(inc.timeline.slice(0, step + 1));
            
            step++;
        }, 500); // 500ms delay per agent execution block
    }

    async function handleProjectDiscovery() {
        const projectId = projectIdInput ? projectIdInput.value.trim() : "";
        if (!projectId) {
            alert("Please provide a valid GCP Project ID.");
            return;
        }
        
        if (discoveredResourcesSection) {
            discoveredResourcesSection.style.display = "block";
        }
        if (discoveredResourcesList) {
            discoveredResourcesList.innerHTML = `<li class="loading-placeholder">Discovering resources on project '${projectId}'...</li>`;
        }
        if (discoveryVulnerabilityBadge) {
            discoveryVulnerabilityBadge.style.display = "none";
        }
        
        try {
            const res = await fetch(`/api/projects/${encodeURIComponent(projectId)}/discover`);
            const data = await res.json();
            
            if (data.error) {
                if (discoveredResourcesList) {
                    discoveredResourcesList.innerHTML = `<li class="loading-placeholder text-danger">Error: ${data.error}</li>`;
                }
                return;
            }
            
            renderDiscoveredResources(data.resources);
        } catch (err) {
            console.error("Discovery request failed:", err);
            if (discoveredResourcesList) {
                discoveredResourcesList.innerHTML = `<li class="loading-placeholder text-danger">Failed to connect to discovery server.</li>`;
            }
        }
    }
    
    function renderDiscoveredResources(resources) {
        if (!discoveredResourcesList) return;
        discoveredResourcesList.innerHTML = "";
        
        if (!resources || resources.length === 0) {
            discoveredResourcesList.innerHTML = `<li class="loading-placeholder">No active GCP resources discovered.</li>`;
            if (discoveryVulnerabilityBadge) discoveryVulnerabilityBadge.style.display = "none";
            return;
        }
        
        let hasVulnerability = false;
        
        const typeIcons = {
            "gce_vm": "🖥️",
            "cloud_run": "🏃",
            "gke_cluster": "☸️",
            "cloud_sql": "💾"
        };
        
        const typeNames = {
            "gce_vm": "GCE VM",
            "cloud_run": "Cloud Run",
            "gke_cluster": "GKE Cluster",
            "cloud_sql": "Cloud SQL"
        };
        
        resources.forEach(r => {
            const isVulnerable = !!r.vulnerable;
            if (isVulnerable) hasVulnerability = true;
            
            const item = document.createElement("li");
            item.className = `discovered-resource-item ${isVulnerable ? "vulnerable" : "safe"}`;
            
            const icon = typeIcons[r.type] || "☁️";
            const typeName = typeNames[r.type] || r.type;
            
            item.innerHTML = `
                <div class="resource-info">
                    <div class="resource-icon">${icon}</div>
                    <div class="resource-details">
                        <span class="resource-name">${escapeHTML(r.name)}</span>
                        <span class="resource-type-loc">${typeName} | ${escapeHTML(r.location)}</span>
                    </div>
                </div>
                <div class="resource-status-container">
                    ${isVulnerable ? `<span class="resource-warning-icon" title="${escapeHTML(r.warning)}">⚠️</span>` : ""}
                    <span class="status-badge ${r.status === 'RUNNING' || r.status === 'READY' ? 'status-active' : 'status-unknown'}">${escapeHTML(r.status)}</span>
                </div>
            `;
            
            discoveredResourcesList.appendChild(item);
        });
        
        if (discoveryVulnerabilityBadge) {
            discoveryVulnerabilityBadge.style.display = hasVulnerability ? "inline-block" : "none";
        }
    }
    
    function escapeHTML(str) {
        if (!str) return "";
        return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
    }
});
