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
    const projectIdsList = document.getElementById("project-ids-list");
    const projectHistoryList = document.getElementById("project-history-list");
    let projectHistory = [];
    
    // Project View Big Page Elements
    const projectDiscoveryView = document.getElementById("project-discovery-view");
    const incidentDashboardView = document.getElementById("incident-dashboard-view");
    const btnCloseProjectView = document.getElementById("btn-close-project-view");
    
    const projectViewTitle = document.getElementById("project-view-title");
    const projectCachePath = document.getElementById("project-cache-path");
    const projectComplianceBadge = document.getElementById("project-compliance-badge");
    
    const statTotalResources = document.getElementById("stat-total-resources");
    const statExposedResources = document.getElementById("stat-exposed-resources");
    const statSafeResources = document.getElementById("stat-safe-resources");
    const statLastAudit = document.getElementById("stat-last-audit");
    
    const assetsListVm = document.getElementById("assets-list-vm");
    const assetsListRun = document.getElementById("assets-list-run");
    const assetsListGke = document.getElementById("assets-list-gke");
    const assetsListSql = document.getElementById("assets-list-sql");
    const assetsListBucket = document.getElementById("assets-list-bucket");
    const assetsListNetwork = document.getElementById("assets-list-network");
    
    // Verbose Vulnerabilities Modal Elements
    const vulnerabilitiesModal = document.getElementById("vulnerabilities-modal");
    const btnCloseModal = document.getElementById("btn-close-modal");
    const modalVulnsBody = document.getElementById("modal-vulns-body");
    const warningStatBox = document.querySelector(".stat-box.warning-state");
    
    // Chat DOM Elements
    const chatMessagesContainer = document.getElementById("chat-messages-container");
    const chatUserInput = document.getElementById("chat-user-input");
    const btnChatSend = document.getElementById("btn-chat-send");
    
    let activeIncidentId = null;
    let currentProjectResources = []; // Dynamic cache of loaded resources for modal display
    
    // Initialize
    loadConfig();
    loadIncidentRepository();
    
    // Event Listeners
    btnTrigger.addEventListener("click", triggerLiveSimulation);
    if (btnApprove) btnApprove.addEventListener("click", approveMutation);
    if (btnReject) btnReject.addEventListener("click", rejectMutation);
    if (btnChatSend) btnChatSend.addEventListener("click", sendChatMessage);
    if (btnDiscoverProject) btnDiscoverProject.addEventListener("click", handleProjectDiscovery);
    
    // Close modal action
    if (btnCloseModal && vulnerabilitiesModal) {
        btnCloseModal.addEventListener("click", () => {
            vulnerabilitiesModal.classList.remove("active");
            setTimeout(() => {
                vulnerabilitiesModal.style.display = "none";
            }, 300);
        });
        
        // Close modal when clicking outside contents
        vulnerabilitiesModal.addEventListener("click", (e) => {
            if (e.target === vulnerabilitiesModal) {
                vulnerabilitiesModal.classList.remove("active");
                setTimeout(() => {
                    vulnerabilitiesModal.style.display = "none";
                }, 300);
            }
        });
    }
    
    if (warningStatBox) {
        warningStatBox.addEventListener("click", () => {
            const projectId = projectIdInput ? projectIdInput.value.trim() : "Unknown";
            openVulnerabilitiesReport(projectId, currentProjectResources);
        });
    }
    
    if (btnCloseProjectView) {
        btnCloseProjectView.addEventListener("click", () => {
            if (incidentDashboardView && projectDiscoveryView) {
                incidentDashboardView.style.display = "block";
                projectDiscoveryView.style.display = "none";
            }
        });
    }
    
    const projectLabel = document.querySelector('label[for="project-id-input"]');
    if (projectLabel) {
        projectLabel.style.cursor = "pointer";
        projectLabel.addEventListener("click", handleProjectDiscovery);
    }

    // Wire collapsible panel headers
    document.querySelectorAll(".asset-panel .clickable-header").forEach(header => {
        header.addEventListener("click", () => {
            const panel = header.closest(".asset-panel");
            const btn = header.querySelector(".panel-toggle-btn");
            const isCollapsed = panel.classList.toggle("collapsed");
            if (btn) {
                btn.textContent = isCollapsed ? "▶" : "▼";
            }
        });
    });
    
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
                
                // Load cached project history from local storage
                const cachedHistory = localStorage.getItem("benjamin_project_history");
                if (cachedHistory) {
                    try {
                        projectHistory = JSON.parse(cachedHistory);
                    } catch (e) {
                        projectHistory = [];
                    }
                }
                
                // Keep the .env default project ID always at the top of the history list
                if (!projectHistory.includes(data.project_id)) {
                    projectHistory.unshift(data.project_id);
                    localStorage.setItem("benjamin_project_history", JSON.stringify(projectHistory));
                }
                
                updateProjectHistoryList();
                
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
                    if (incidentDashboardView && projectDiscoveryView) {
                        incidentDashboardView.style.display = "block";
                        projectDiscoveryView.style.display = "none";
                    }
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
        if (incidentDashboardView && projectDiscoveryView) {
            incidentDashboardView.style.display = "block";
            projectDiscoveryView.style.display = "none";
        }
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
        
        // Show right-hand side view
        if (projectDiscoveryView && incidentDashboardView) {
            incidentDashboardView.style.display = "none";
            projectDiscoveryView.style.display = "flex";
        }
        
        if (projectViewTitle) projectViewTitle.textContent = `GCP PROJECT ASSETS: ${projectId}`;
        if (projectCachePath) projectCachePath.textContent = `discover/gcp-project/${projectId}.json`;
        
        // Show placeholders
        if (assetsListVm) assetsListVm.innerHTML = `<p class="loading-placeholder">Discovering VM instances on '${projectId}'...</p>`;
        if (assetsListRun) assetsListRun.innerHTML = `<p class="loading-placeholder">Discovering Cloud Run services on '${projectId}'...</p>`;
        if (assetsListGke) assetsListGke.innerHTML = `<p class="loading-placeholder">Discovering GKE clusters on '${projectId}'...</p>`;
        if (assetsListSql) assetsListSql.innerHTML = `<p class="loading-placeholder">Discovering Cloud SQL instances on '${projectId}'...</p>`;
        
        try {
            const res = await fetch(`/api/projects/${encodeURIComponent(projectId)}/discover`);
            const data = await res.json();
            
            if (data.error) {
                const errMsg = `<p class="loading-placeholder text-danger">Error: ${data.error}</p>`;
                if (assetsListVm) assetsListVm.innerHTML = errMsg;
                if (assetsListRun) assetsListRun.innerHTML = errMsg;
                if (assetsListGke) assetsListGke.innerHTML = errMsg;
                if (assetsListSql) assetsListSql.innerHTML = errMsg;
                return;
            }
            
            renderBigProjectPage(projectId, data);
            saveToProjectHistory(projectId);
            
            // Highlight selection in the left sidebar projects list
            document.querySelectorAll(".project-history-item").forEach(item => {
                if (item.dataset.id === projectId) {
                    item.classList.add("active");
                } else {
                    item.classList.remove("active");
                }
            });
        } catch (err) {
            console.error("Discovery request failed:", err);
            const errMsg = `<p class="loading-placeholder text-danger">Failed to connect to discovery server.</p>`;
            if (assetsListVm) assetsListVm.innerHTML = errMsg;
            if (assetsListRun) assetsListRun.innerHTML = errMsg;
            if (assetsListGke) assetsListGke.innerHTML = errMsg;
            if (assetsListSql) assetsListSql.innerHTML = errMsg;
        }
    }
    
    function escapeHTML(str) {
        if (!str) return "";
        return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
    }

    function saveToProjectHistory(projectId) {
        if (!projectId) return;
        if (!projectHistory.includes(projectId)) {
            projectHistory.push(projectId);
            localStorage.setItem("benjamin_project_history", JSON.stringify(projectHistory));
            updateProjectHistoryList();
        }
    }
    
    function updateProjectHistoryList() {
        // Update autocomplete suggestions
        if (projectIdsList) {
            projectIdsList.innerHTML = "";
            projectHistory.forEach(pid => {
                const option = document.createElement("option");
                option.value = pid;
                projectIdsList.appendChild(option);
            });
        }
        
        // Update clickable projects list in left sidebar
        if (projectHistoryList) {
            projectHistoryList.innerHTML = "";
            if (projectHistory.length === 0) {
                projectHistoryList.innerHTML = `<li class="loading-placeholder">No projects recorded</li>`;
                return;
            }
            
            projectHistory.forEach(pid => {
                const li = document.createElement("li");
                li.className = "project-history-item";
                li.dataset.id = pid;
                
                li.innerHTML = `
                    <span class="project-history-icon">☁️</span>
                    <span class="project-history-id">${escapeHTML(pid)}</span>
                `;
                
                li.addEventListener("click", () => {
                    document.querySelectorAll(".project-history-item").forEach(item => item.classList.remove("active"));
                    li.classList.add("active");
                    if (projectIdInput) {
                        projectIdInput.value = pid;
                    }
                    handleProjectDiscovery();
                });
                
                projectHistoryList.appendChild(li);
            });
        }
    }

    function renderBigProjectPage(projectId, data) {
        if (incidentDashboardView && projectDiscoveryView) {
            incidentDashboardView.style.display = "none";
            projectDiscoveryView.style.display = "flex";
        }
        
        if (projectViewTitle) projectViewTitle.textContent = `GCP PROJECT ASSETS: ${projectId}`;
        if (projectCachePath) projectCachePath.textContent = `discover/gcp-project/${projectId}.json`;
        
        const resources = data.resources || [];
        currentProjectResources = resources; // Cache globally for the interactive modal
        
        const total = resources.length;
        const exposed = resources.filter(r => r.vulnerable).length;
        const safe = total - exposed;
        
        if (statTotalResources) statTotalResources.textContent = total;
        if (statExposedResources) statExposedResources.textContent = exposed;
        if (statSafeResources) statSafeResources.textContent = safe;
        if (statLastAudit) {
            statLastAudit.textContent = new Date().toLocaleTimeString();
        }
        
        if (projectComplianceBadge) {
            if (exposed > 0) {
                projectComplianceBadge.textContent = "🚨 AUDIT WARNING";
                projectComplianceBadge.className = "compliance-badge badge-warning";
            } else {
                projectComplianceBadge.textContent = "✅ COMPLIANT";
                projectComplianceBadge.className = "compliance-badge badge-safe";
            }
        }

        // Configure clickability of Exposed/Vulnerable stat card
        if (warningStatBox) {
            if (exposed > 0) {
                warningStatBox.classList.add("has-vulns");
                warningStatBox.title = "⚠️ Click to open full verbose vulnerabilities report";
            } else {
                warningStatBox.classList.remove("has-vulns");
                warningStatBox.removeAttribute("title");
            }
        }

        // Live vs Mock Telemetry Indicator
        const projectStatusBanner = document.getElementById("project-status-banner");
        if (projectStatusBanner) {
            const hasMock = resources.some(r => r.is_mock === true);
            if (hasMock || resources.length === 0) {
                projectStatusBanner.style.display = "flex";
                projectStatusBanner.className = "project-status-banner mock-active";
                projectStatusBanner.innerHTML = `<span>⚠️ DEMO / MOCK DATA ACTIVATED: The application is running in mock/demo mode because MOCK_TOOLING=true or live discovery failed/lacks permissions.</span>`;
            } else {
                projectStatusBanner.style.display = "flex";
                projectStatusBanner.className = "project-status-banner live-active";
                projectStatusBanner.innerHTML = `<span>🟢 LIVE PRODUCTION AUDIT: Successfully fetched live resources from Google Cloud API using active Service Account credentials.</span>`;
            }
        }
        
        // Clear all list containers
        if (assetsListVm) assetsListVm.innerHTML = "";
        if (assetsListRun) assetsListRun.innerHTML = "";
        if (assetsListGke) assetsListGke.innerHTML = "";
        if (assetsListSql) assetsListSql.innerHTML = "";
        if (assetsListBucket) assetsListBucket.innerHTML = "";
        if (assetsListNetwork) assetsListNetwork.innerHTML = "";
        
        // Group and render each asset type
        const vmAssets = resources.filter(r => r.type === "gce_vm");
        const runAssets = resources.filter(r => r.type === "cloud_run");
        const gkeAssets = resources.filter(r => r.type === "gke_cluster");
        const sqlAssets = resources.filter(r => r.type === "cloud_sql");
        const bucketAssets = resources.filter(r => r.type === "gcs_bucket");
        const networkAssets = resources.filter(r => r.type === "vpc_network");
        
        renderAssetGroup(projectId, vmAssets, assetsListVm, "🖥️ GCE VM Instance", r => `
            <div class="asset-meta-item"><span class="asset-meta-label">Zone:</span> <span class="asset-meta-value">${escapeHTML(r.location)}</span></div>
            <div class="asset-meta-item"><span class="asset-meta-label">Internal IP:</span> <span class="asset-meta-value">${escapeHTML(r.metadata.internal_ip || 'N/A')}</span></div>
            <div class="asset-meta-item"><span class="asset-meta-label">External IP:</span> <span class="asset-meta-value">${escapeHTML(r.metadata.external_ip || 'None')}</span></div>
        `);
        
        renderAssetGroup(projectId, runAssets, assetsListRun, "🏃 Cloud Run Service", r => `
            <div class="asset-meta-item"><span class="asset-meta-label">Region:</span> <span class="asset-meta-value">${escapeHTML(r.location)}</span></div>
            <div class="asset-meta-item"><span class="asset-meta-label">Service URL:</span> <a href="${escapeHTML(r.metadata.url)}" target="_blank" class="asset-meta-value text-cyan" style="word-break: break-all;">${escapeHTML(r.metadata.url || 'N/A')}</a></div>
            <div class="asset-meta-item"><span class="asset-meta-label">Public Access:</span> <span class="asset-meta-value">${r.metadata.all_users_invoker ? 'Enabled (unauthenticated)' : 'Disabled (secured)'}</span></div>
        `);
        
        renderAssetGroup(projectId, gkeAssets, assetsListGke, "☸️ GKE Cluster", r => `
            <div class="asset-meta-item"><span class="asset-meta-label">Location:</span> <span class="asset-meta-value">${escapeHTML(r.location)}</span></div>
            <div class="asset-meta-item"><span class="asset-meta-label">Control Endpoint:</span> <span class="asset-meta-value">${escapeHTML(r.metadata.endpoint || 'N/A')}</span></div>
            <div class="asset-meta-item"><span class="asset-meta-label">Boundary Security:</span> <span class="asset-meta-value">${r.metadata.private_cluster ? 'Private Cluster Enabled' : 'Public Control Plane Exposure'}</span></div>
        `);
        
        renderAssetGroup(projectId, sqlAssets, assetsListSql, "💾 Cloud SQL Instance", r => `
            <div class="asset-meta-item"><span class="asset-meta-label">Region:</span> <span class="asset-meta-value">${escapeHTML(r.location)}</span></div>
            <div class="asset-meta-item"><span class="asset-meta-label">Public Access:</span> <span class="asset-meta-value">${r.metadata.public_ip_enabled ? 'Enabled' : 'Disabled (Private IP only)'}</span></div>
            <div class="asset-meta-item"><span class="asset-meta-label">Authorized Networks:</span> <span class="asset-meta-value">${r.metadata.authorized_networks && r.metadata.authorized_networks.length > 0 ? escapeHTML(r.metadata.authorized_networks.join(', ')) : 'None (open or private)'}</span></div>
        `);

        renderAssetGroup(projectId, bucketAssets, assetsListBucket, "🪣 GCS Storage Bucket", r => `
            <div class="asset-meta-item"><span class="asset-meta-label">Location:</span> <span class="asset-meta-value">${escapeHTML(r.location)}</span></div>
            <div class="asset-meta-item"><span class="asset-meta-label">Storage Class:</span> <span class="asset-meta-value">${escapeHTML(r.metadata.storage_class || 'STANDARD')}</span></div>
            <div class="asset-meta-item"><span class="asset-meta-label">Public Prevention:</span> <span class="asset-meta-value">${escapeHTML(r.metadata.public_access_prevention || 'inherited')}</span></div>
        `);
        
        renderAssetGroup(projectId, networkAssets, assetsListNetwork, "🌐 VPC Network", r => `
            <div class="asset-meta-item"><span class="asset-meta-label">Subnets count:</span> <span class="asset-meta-value">${r.metadata.subnetworks ? r.metadata.subnetworks.length : 0}</span></div>
            <div class="asset-meta-item"><span class="asset-meta-label">Routing Mode:</span> <span class="asset-meta-value">${escapeHTML(r.metadata.routing_mode || 'REGIONAL')}</span></div>
            <div class="asset-meta-item"><span class="asset-meta-label">Auto-Subnets Mode:</span> <span class="asset-meta-value">${r.metadata.auto_create_subnetworks ? 'Enabled (Auto)' : 'Disabled (Custom subnets)'}</span></div>
        `);
    }
    
    function renderAssetGroup(projectId, assets, container, typeName, metaHtmlBuilder) {
        if (!container) return;
        if (assets.length === 0) {
            container.innerHTML = `<p class="loading-placeholder">No active ${escapeHTML(typeName)} instances found.</p>`;
            return;
        }
        
        assets.forEach((r, idx) => {
            const card = document.createElement("div");
            card.className = `asset-card ${r.vulnerable ? 'vulnerable' : 'safe'}`;
            
            // Build red hover indicator emoji next to title if resource is vulnerable
            const warningIconHtml = r.vulnerable ? `
                <span class="vuln-hover-icon" title="⚠️ Click to open full verbose vulnerabilities report&#10;&#10;Problem: ${escapeHTML(r.warning)}">🚨</span>
            ` : '';

            card.innerHTML = `
                <div class="asset-card-header">
                    <div style="display: flex; align-items: center; gap: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                        <span class="asset-card-title">${escapeHTML(r.name)}</span>
                        ${warningIconHtml}
                    </div>
                    <span class="status-badge ${r.status === 'RUNNING' || r.status === 'READY' ? 'status-active' : 'status-unknown'}">${escapeHTML(r.status)}</span>
                </div>
                <div class="asset-card-body">
                    ${metaHtmlBuilder(r)}
                    
                    ${r.console_url ? `
                        <div class="asset-meta-item" style="margin-top: 10px; display: flex; align-items: center; border-top: 1px dashed rgba(255, 255, 255, 0.05); padding-top: 8px;">
                            <a href="${escapeHTML(r.console_url)}" target="_blank" class="text-cyan" style="display: inline-flex; align-items: center; gap: 6px; text-decoration: underline; font-size: 12px; font-weight: 600;">
                                🔗 Open in GCP Console
                            </a>
                        </div>
                    ` : ''}
                    
                    <span class="asset-metadata-toggle" style="margin-top: 8px;">View raw metadata</span>
                    <pre class="asset-metadata-content" style="display: none; margin-top: 6px;">${escapeHTML(JSON.stringify(r.metadata, null, 2))}</pre>
                </div>
            `;
            
            // Wire warning icon click to open modal
            const vulnIcon = card.querySelector(".vuln-hover-icon");
            if (vulnIcon) {
                vulnIcon.addEventListener("click", (e) => {
                    e.stopPropagation();
                    openVulnerabilitiesReport(projectId, currentProjectResources);
                });
            }

            // Wire metadata toggle
            const toggle = card.querySelector(".asset-metadata-toggle");
            const metadataBlock = card.querySelector(".asset-metadata-content");
            if (toggle && metadataBlock) {
                toggle.addEventListener("click", () => {
                    const isHidden = metadataBlock.style.display === "none";
                    metadataBlock.style.display = isHidden ? "block" : "none";
                    toggle.textContent = isHidden ? "Hide raw metadata" : "View raw metadata";
                });
            }
            
            container.appendChild(card);
        });
    }

    // Opens a verbose, full-page vulnerabilities report modal for deep diagnostics
    function openVulnerabilitiesReport(projectId, resources) {
        if (!modalVulnsBody || !vulnerabilitiesModal) return;
        
        const vulns = resources.filter(r => r.vulnerable);
        if (vulns.length === 0) {
            modalVulnsBody.innerHTML = `<p class="loading-placeholder">🟢 No security warnings detected! Project '${escapeHTML(projectId)}' is completely compliant and secure.</p>`;
        } else {
            modalVulnsBody.innerHTML = "";
            vulns.forEach(r => {
                const item = document.createElement("div");
                item.className = "vuln-report-item";
                item.innerHTML = `
                    <div class="vuln-report-header">
                        <span class="vuln-report-title">${escapeHTML(r.name)}</span>
                        <span class="vuln-report-badge">${escapeHTML(r.type.replace('_', ' '))}</span>
                    </div>
                    <div class="vuln-report-desc">
                        🚨 <strong>Vulnerability Warning:</strong> ${escapeHTML(r.warning)}
                    </div>
                    <div class="vuln-report-meta">
                        <div class="asset-meta-item"><span class="asset-meta-label">Location:</span> <span class="asset-meta-value">${escapeHTML(r.location)}</span></div>
                        <div class="asset-meta-item"><span class="asset-meta-label">Status:</span> <span class="asset-meta-value">${escapeHTML(r.status)}</span></div>
                        ${r.console_url ? `
                            <div class="asset-meta-item" style="margin-top: 6px;">
                                <a href="${escapeHTML(r.console_url)}" target="_blank" class="text-cyan" style="display: inline-flex; align-items: center; gap: 6px; text-decoration: underline; font-weight: 600;">
                                    🔗 Open in GCP Console
                                </a>
                            </div>
                        ` : ''}
                    </div>
                    <span class="asset-metadata-toggle" style="margin-top: 8px;">View raw metadata</span>
                    <pre class="asset-metadata-content" style="display: none; margin-top: 6px;">${escapeHTML(JSON.stringify(r.metadata, null, 2))}</pre>
                `;
                
                // Wire metadata toggle inside modal report items
                const toggle = item.querySelector(".asset-metadata-toggle");
                const metadataBlock = item.querySelector(".asset-metadata-content");
                if (toggle && metadataBlock) {
                    toggle.addEventListener("click", () => {
                        const isHidden = metadataBlock.style.display === "none";
                        metadataBlock.style.display = isHidden ? "block" : "none";
                        toggle.textContent = isHidden ? "Hide raw metadata" : "View raw metadata";
                    });
                }
                
                modalVulnsBody.appendChild(item);
            });
        }
        
        vulnerabilitiesModal.style.display = "flex";
        setTimeout(() => {
            vulnerabilitiesModal.classList.add("active");
        }, 10);
    }
});
