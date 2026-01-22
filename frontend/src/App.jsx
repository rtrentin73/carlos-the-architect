import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import mermaid from 'mermaid';
import { Layout, Send, Cloud, ShieldCheck, PenTool, Loader2, MessageCircle, Activity } from 'lucide-react';
import Splash from './components/Splash';

export default function App() {
  const [showSplash, setShowSplash] = useState(true);
  const [input, setInput] = useState("");
  const [scenario, setScenario] = useState("custom");
  const [costPerformance, setCostPerformance] = useState("balanced");
  const [complianceLevel, setComplianceLevel] = useState("standard");
  const [reliabilityLevel, setReliabilityLevel] = useState("normal");
  const [strictnessLevel, setStrictnessLevel] = useState("balanced");
 
  const backendBaseUrl = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";
  const [design, setDesign] = useState("");
  const [roneiDesign, setRoneiDesign] = useState("");
  const [isDesigning, setIsDesigning] = useState(false);
  const [auditStatus, setAuditStatus] = useState("");
  const [auditReport, setAuditReport] = useState("");
  const [securityReport, setSecurityReport] = useState("");
  const [costReport, setCostReport] = useState("");
  const [reliabilityReport, setReliabilityReport] = useState("");
  const [agentChat, setAgentChat] = useState("");
  const [currentView, setCurrentView] = useState("blueprint");
  const [blueprintTab, setBlueprintTab] = useState("carlos");
  const [history, setHistory] = useState(() => {
    const saved = localStorage.getItem("designHistory");
    return saved ? JSON.parse(saved) : [];
  });
  const [activityLog, setActivityLog] = useState([]);
  const [agentStatuses, setAgentStatuses] = useState({
    design: 'pending',
    ronei_design: 'pending',
    security: 'pending',
    cost: 'pending',
    reliability: 'pending',
    audit: 'pending',
    recommender: 'pending'
  });
  const [tokenCounts, setTokenCounts] = useState({
    carlos: 0,
    ronei_design: 0
  });

  useEffect(() => {
    const timer = setTimeout(() => setShowSplash(false), 3000);
    return () => clearTimeout(timer);
  }, []);

  const handleStreamEvent = (event) => {
    const agentDescriptions = {
      design: 'Carlos (Lead Cloud Architect) - Designing cloud infrastructure',
      ronei_design: 'Ronei (Rival Architect) - Creating alternative modern design',
      security: 'Security Analyst - Reviewing security posture',
      cost: 'Cost Optimization Specialist - Analyzing cost efficiency',
      reliability: 'SRE - Evaluating reliability and operations',
      audit: 'Chief Auditor - Performing final audit review',
      recommender: 'Design Recommender - Choosing best design approach'
    };

    switch (event.type) {
      case "agent_start":
        console.log(`🚀 Agent ${event.agent} started`);
        setActivityLog(prev => [...prev, {
          id: Date.now() + Math.random(),
          type: 'start',
          agent: event.agent,
          message: agentDescriptions[event.agent] || `Agent ${event.agent} started`,
          timestamp: event.timestamp || new Date().toISOString()
        }]);
        setAgentStatuses(prev => ({ ...prev, [event.agent]: 'active' }));
        break;

      case "agent_complete":
        console.log(`✅ Agent ${event.agent} completed`);
        setActivityLog(prev => [...prev, {
          id: Date.now() + Math.random(),
          type: 'complete',
          agent: event.agent,
          message: `${event.agent} completed successfully`,
          timestamp: event.timestamp || new Date().toISOString()
        }]);
        setAgentStatuses(prev => ({ ...prev, [event.agent]: 'completed' }));
        break;

      case "token":
        if (event.agent === "carlos") {
          setDesign(prev => prev + event.content);
          setTokenCounts(prev => ({ ...prev, carlos: prev.carlos + 1 }));

          // Add streaming indicator to activity log (update every 50 tokens to avoid spam)
          setTokenCounts(prev => {
            const newCount = prev.carlos + 1;
            if (newCount % 50 === 0) {
              setActivityLog(activityPrev => [...activityPrev, {
                id: Date.now() + Math.random(),
                type: 'streaming',
                agent: 'carlos',
                message: `Carlos streaming design... (${newCount} tokens)`,
                timestamp: event.timestamp || new Date().toISOString()
              }]);
            }
            return { ...prev, carlos: newCount };
          });
        } else if (event.agent === "ronei_design") {
          setRoneiDesign(prev => prev + event.content);
          setTokenCounts(prev => ({ ...prev, ronei_design: prev.ronei_design + 1 }));

          // Add streaming indicator to activity log (update every 50 tokens to avoid spam)
          setTokenCounts(prev => {
            const newCount = prev.ronei_design + 1;
            if (newCount % 50 === 0) {
              setActivityLog(activityPrev => [...activityPrev, {
                id: Date.now() + Math.random(),
                type: 'streaming',
                agent: 'ronei_design',
                message: `Ronei streaming design... (${newCount} tokens)`,
                timestamp: event.timestamp || new Date().toISOString()
              }]);
            }
            return { ...prev, ronei_design: newCount };
          });
        }
        break;

      case "field_update":
        const fieldLabels = {
          security_report: 'Security Analysis Report',
          cost_report: 'Cost Optimization Report',
          reliability_report: 'Reliability & Operations Report',
          audit_report: 'Chief Auditor Verdict',
          audit_status: 'Audit Status',
          recommendation: 'Design Recommendation'
        };

        // Add to activity log
        const preview = event.content ? event.content.substring(0, 150) + '...' : '';
        setActivityLog(prev => [...prev, {
          id: Date.now() + Math.random(),
          type: 'report',
          agent: event.field,
          message: `${fieldLabels[event.field] || event.field} generated`,
          detail: preview,
          timestamp: event.timestamp || new Date().toISOString()
        }]);

        // Update state
        switch (event.field) {
          case "security_report":
            setSecurityReport(event.content);
            break;
          case "cost_report":
            setCostReport(event.content);
            break;
          case "reliability_report":
            setReliabilityReport(event.content);
            break;
          case "audit_report":
            setAuditReport(event.content);
            break;
          case "audit_status":
            setAuditStatus(event.content);
            break;
          case "recommendation":
            console.log("Recommendation received:", event.content);
            break;
        }
        break;

      case "complete":
        console.log("🎉 Design generation complete!");
        const summary = event.summary;

        // Save to history
        const newEntry = {
          id: Date.now(),
          requirements: input,
          scenario,
          costPerformance,
          complianceLevel,
          reliabilityLevel,
          strictnessLevel,
          design: summary.design,
          roneiDesign: summary.ronei_design || "",
          auditStatus: summary.audit_status || "",
          auditReport: summary.audit_report || "",
          securityReport: summary.security_report || "",
          costReport: summary.cost_report || "",
          reliabilityReport: summary.reliability_report || "",
          agentChat: summary.agent_chat || "",
          timestamp: new Date().toLocaleString()
        };
        const updatedHistory = [newEntry, ...history];
        setHistory(updatedHistory);
        localStorage.setItem("designHistory", JSON.stringify(updatedHistory));
        setAgentChat(summary.agent_chat || "");
        break;

      case "error":
        console.error("❌ Stream error:", event.message);
        setDesign(`Error: ${event.message}`);
        setActivityLog(prev => [...prev, {
          id: Date.now() + Math.random(),
          type: 'error',
          agent: 'system',
          message: `Error: ${event.message}`,
          timestamp: event.timestamp || new Date().toISOString()
        }]);
        setIsDesigning(false);
        break;
    }
  };

  const handleAskCarlos = async () => {
    // Reset all state
    setDesign("");
    setRoneiDesign("");
    setSecurityReport("");
    setCostReport("");
    setReliabilityReport("");
    setAuditReport("");
    setAuditStatus("");
    setAgentChat("");
    setActivityLog([]);
    setAgentStatuses({
      design: 'pending',
      ronei_design: 'pending',
      security: 'pending',
      cost: 'pending',
      reliability: 'pending',
      audit: 'pending',
      recommender: 'pending'
    });
    setTokenCounts({
      carlos: 0,
      ronei_design: 0
    });
    setIsDesigning(true);

    console.log("=== Starting streaming design request ===");
    console.log("Input:", input);

    try {
      console.log(`Streaming from ${backendBaseUrl}/design-stream`);
      const response = await fetch(`${backendBaseUrl}/design-stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: input,
          scenario,
          priorities: {
            cost_performance: costPerformance,
            compliance: complianceLevel,
            reliability: reliabilityLevel,
            strictness: strictnessLevel,
          },
        }),
      });

      console.log("Response status:", response.status);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Read SSE stream
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");

        // Keep incomplete line in buffer
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const jsonStr = line.substring(6).trim();
            if (jsonStr === "") continue;

            try {
              const event = JSON.parse(jsonStr);
              handleStreamEvent(event);
            } catch (e) {
              console.error("Failed to parse SSE event:", e, jsonStr);
            }
          }
        }
      }
    } catch (error) {
      console.error("Error streaming design:", error);
      setDesign("Error: Unable to generate design. Please check the backend and try again.");
    } finally {
      setIsDesigning(false);
      console.log("=== Design request complete ===");
    }
  };

  const handleDownloadBlueprint = () => {
    if (!design) return;

    const timestamp = new Date().toISOString();
    const scenarioLabel =
      scenario === "public_web_app"
        ? "Public Web App"
        : scenario === "data_pipeline"
        ? "Data Pipeline / Analytics"
        : scenario === "event_driven"
        ? "Event-driven Microservices"
        : "Custom";

    const content = [
      "# Carlos & Ronei Cloud Blueprint",
      "",
      `Generated: ${timestamp}`,
      "",
      "## Requirements",
      "",
      input || "(No requirements captured)",
      "",
      "## Scenario & Priorities",
      "",
      `- Scenario: ${scenarioLabel}`,
      `- Cost vs Performance: ${costPerformance}`,
      `- Compliance Level: ${complianceLevel}`,
      `- Reliability Target: ${reliabilityLevel}`,
      "",
      "## Carlos' Design",
      "",
      design || "_Carlos' design not generated._",
      "",
      "## Ronei's Design",
      "",
      roneiDesign || "_Ronei's design not generated._",
      "",
      "## Security Analyst Report",
      "",
      securityReport || "_No security report generated._",
      "",
      "## Cost Optimization Report",
      "",
      costReport || "_No cost optimization report generated._",
      "",
      "## Reliability & Operations Report",
      "",
      reliabilityReport || "_No reliability report generated._",
      "",
      "## Chief Auditor Verdict",
      "",
      auditReport || "_No final audit verdict generated._",
      "",
      "## Agent Conversation",
      "",
      agentChat || "_No agent conversation captured._",
      "",
    ].join("\n");

    const blob = new Blob([content], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `carlos-blueprint-${timestamp.replace(/[:T]/g, "-").slice(0, 19)}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (showSplash) return <Splash />;

  return (
    <div className="flex h-screen bg-slate-50">
      {/* Sidebar Navigation */}
      <aside className="w-64 bg-slate-900 text-white p-6 flex flex-col">
        <div className="flex items-center gap-3 mb-10">
          <div className="bg-blue-500 p-2 rounded-lg"><Layout size={20}/></div>
          <span className="font-bold text-xl text-white whitespace-nowrap">Carlos AI</span>
        </div>
        <nav className="space-y-4">
          <NavItem icon={<PenTool size={18}/>} label="New Blueprint" active={currentView === "blueprint"} onClick={() => setCurrentView("blueprint")} />
          <NavItem icon={<Activity size={18}/>} label="Live Activity" active={currentView === "activity"} onClick={() => setCurrentView("activity")} />
          <NavItem icon={<Cloud size={18}/>} label="Cloud History" active={currentView === "history"} onClick={() => setCurrentView("history")} />
          <NavItem icon={<ShieldCheck size={18}/>} label="Security Audits" active={currentView === "audits"} onClick={() => setCurrentView("audits")} />
          <NavItem icon={<MessageCircle size={18}/>} label="Agent Chat" active={currentView === "agents"} onClick={() => setCurrentView("agents")} />
          <NavItem icon={<Layout size={18}/>} label="Help & Agents" active={currentView === "help"} onClick={() => setCurrentView("help")} />
          <NavItem icon={<Cloud size={18}/>} label="Analytics" active={currentView === "analytics"} onClick={() => setCurrentView("analytics")} />
        </nav>
      </aside>

      {/* Main Design Area */}
      <main className="flex-1 flex flex-col">
        <div className="flex-1 overflow-y-auto p-12">
          <div className="max-w-3xl mx-auto bg-white shadow-xl rounded-2xl p-10 min-h-[80vh] border border-slate-200">
            {currentView === "blueprint" && (
              <>
                <div className="mb-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-500 mb-1 uppercase tracking-wide">
                      Scenario Preset
                    </label>
                    <select
                      className="w-full border rounded-lg px-3 py-2 text-sm bg-white"
                      value={scenario}
                      onChange={(e) => setScenario(e.target.value)}
                    >
                      <option value="custom">Custom</option>
                      <option value="public_web_app">Public Web App</option>
                      <option value="data_pipeline">Data Pipeline / Analytics</option>
                      <option value="event_driven">Event-driven Microservices</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-500 mb-1 uppercase tracking-wide">
                      Cost vs Performance
                    </label>
                    <select
                      className="w-full border rounded-lg px-3 py-2 text-sm bg-white"
                      value={costPerformance}
                      onChange={(e) => setCostPerformance(e.target.value)}
                    >
                      <option value="cost_optimized">Cost-Optimized</option>
                      <option value="balanced">Balanced</option>
                      <option value="performance_optimized">Performance-Optimized</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-500 mb-1 uppercase tracking-wide">
                      Compliance Level
                    </label>
                    <select
                      className="w-full border rounded-lg px-3 py-2 text-sm bg-white"
                      value={complianceLevel}
                      onChange={(e) => setComplianceLevel(e.target.value)}
                    >
                      <option value="standard">Standard</option>
                      <option value="regulated">Regulated (e.g. PCI, HIPAA)</option>
                      <option value="strict">Strict (government / high sensitivity)</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-500 mb-1 uppercase tracking-wide">
                      Reliability Target
                    </label>
                    <select
                      className="w-full border rounded-lg px-3 py-2 text-sm bg-white"
                      value={reliabilityLevel}
                      onChange={(e) => setReliabilityLevel(e.target.value)}
                    >
                      <option value="normal">Normal (99.5–99.9%)</option>
                      <option value="high">High (99.9–99.99%)</option>
                      <option value="extreme">Extreme (multi-region)</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-500 mb-1 uppercase tracking-wide">
                      Design Strictness
                    </label>
                    <select
                      className="w-full border rounded-lg px-3 py-2 text-sm bg-white"
                      value={strictnessLevel}
                      onChange={(e) => setStrictnessLevel(e.target.value)}
                    >
                      <option value="flexible">Flexible (explore options)</option>
                      <option value="balanced">Balanced (managed-first)</option>
                      <option value="strict">Strict (AWS-native, avoid K8s)</option>
                    </select>
                  </div>
                </div>
                {design && (
                  <div className="mb-6 flex justify-end">
                    <button
                      onClick={handleDownloadBlueprint}
                      className="text-xs font-semibold uppercase tracking-wide px-3 py-2 rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-100"
                    >
                      Download Blueprint Package
                    </button>
                  </div>
                )}
                {design || roneiDesign ? (
                  <div>
                    {/* Design Tabs */}
                    <div className="flex border-b border-slate-200 mb-6">
                      <button
                        onClick={() => setBlueprintTab("carlos")}
                        className={`px-4 py-2 font-medium text-sm ${
                          blueprintTab === "carlos"
                            ? "border-b-2 border-blue-500 text-blue-600"
                            : "text-slate-500 hover:text-slate-700"
                        }`}
                      >
                        Carlos' Design
                      </button>
                      <button
                        onClick={() => setBlueprintTab("ronei")}
                        className={`px-4 py-2 font-medium text-sm ${
                          blueprintTab === "ronei"
                            ? "border-b-2 border-purple-500 text-purple-600"
                            : "text-slate-500 hover:text-slate-700"
                        }`}
                      >
                        Ronei's Design
                      </button>
                    </div>
                    
                    {/* Design Content */}
                    {blueprintTab === "carlos" && design && (
                      <BlueprintWithDiagram design={design} />
                    )}
                    {blueprintTab === "ronei" && roneiDesign && (
                      <BlueprintWithDiagram design={roneiDesign} />
                    )}
                    {blueprintTab === "carlos" && !design && (
                      <div className="h-full flex flex-col items-center justify-center text-slate-300">
                        <Cloud size={64} className="mb-4 opacity-20"/>
                        <p className="text-xl italic">Waiting for Carlos' design...</p>
                      </div>
                    )}
                    {blueprintTab === "ronei" && !roneiDesign && (
                      <div className="h-full flex flex-col items-center justify-center text-slate-300">
                        <Cloud size={64} className="mb-4 opacity-20"/>
                        <p className="text-xl italic">Waiting for Ronei's design...</p>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="h-full flex flex-col items-center justify-center text-slate-300">
                    <Cloud size={64} className="mb-4 opacity-20"/>
                    <p className="text-xl italic">Waiting for your requirements...</p>
                  </div>
                )}
              </>
            )}
            {currentView === "activity" && (
              <div>
                <h2 className="text-2xl font-bold mb-6 text-slate-800 flex items-center gap-2">
                  <Activity size={24} className="text-blue-600" />
                  Live Activity Monitor
                </h2>

                {/* Agent Status Overview */}
                <div className="mb-8">
                  <h3 className="text-sm font-semibold text-slate-600 mb-3 uppercase tracking-wide">Agent Status</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {Object.entries(agentStatuses).map(([agent, status]) => (
                      <div
                        key={agent}
                        className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                          status === 'active' ? 'bg-blue-100 text-blue-700 ring-2 ring-blue-400 animate-pulse' :
                          status === 'completed' ? 'bg-green-100 text-green-700' :
                          'bg-gray-100 text-gray-500'
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <div className={`w-2 h-2 rounded-full ${
                            status === 'active' ? 'bg-blue-600' :
                            status === 'completed' ? 'bg-green-600' :
                            'bg-gray-400'
                          }`}></div>
                          <span className="capitalize">{agent.replace('_', ' ')}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Activity Log */}
                <div>
                  <h3 className="text-sm font-semibold text-slate-600 mb-3 uppercase tracking-wide">Activity Log</h3>
                  {activityLog.length === 0 ? (
                    <div className="text-center py-12">
                      <Activity size={48} className="mx-auto text-slate-300 mb-3" />
                      <p className="text-slate-400 italic">
                        {isDesigning ? 'Waiting for agent activity...' : 'No activity yet. Submit a design request to see real-time agent events.'}
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-2 max-h-96 overflow-y-auto bg-slate-50 rounded-lg p-4">
                      {activityLog.map((log) => (
                        <div
                          key={log.id}
                          className={`flex items-start gap-3 p-3 rounded-lg ${
                            log.type === 'start' ? 'bg-blue-50 border-l-4 border-blue-500' :
                            log.type === 'complete' ? 'bg-green-50 border-l-4 border-green-500' :
                            log.type === 'report' ? 'bg-purple-50 border-l-4 border-purple-500' :
                            log.type === 'streaming' ? 'bg-cyan-50 border-l-4 border-cyan-500' :
                            log.type === 'error' ? 'bg-red-50 border-l-4 border-red-500' :
                            'bg-white border-l-4 border-gray-300'
                          }`}
                        >
                          <div className="flex-shrink-0 mt-1">
                            {log.type === 'start' && <span className="text-blue-600 text-xl">🚀</span>}
                            {log.type === 'complete' && <span className="text-green-600 text-xl">✅</span>}
                            {log.type === 'report' && <span className="text-purple-600 text-xl">📄</span>}
                            {log.type === 'streaming' && <span className="text-cyan-600 text-xl">⚡</span>}
                            {log.type === 'error' && <span className="text-red-600 text-xl">❌</span>}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-slate-800">{log.message}</p>
                            {log.detail && (
                              <p className="text-xs text-slate-600 mt-2 p-2 bg-white rounded border border-slate-200 italic">
                                {log.detail}
                              </p>
                            )}
                            <p className="text-xs text-slate-500 mt-1">
                              {new Date(log.timestamp).toLocaleTimeString()}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Instructions */}
                {!isDesigning && activityLog.length === 0 && (
                  <div className="mt-8 p-4 bg-blue-50 rounded-lg border border-blue-200">
                    <p className="text-sm text-blue-800">
                      <strong>💡 Tip:</strong> Go to "New Blueprint" and submit a design request to see real-time agent activity here!
                    </p>
                  </div>
                )}
              </div>
            )}
            {currentView === "history" && (
              <div>
                <h2 className="text-2xl font-bold mb-6 text-slate-800">Design History</h2>
                {history.length === 0 ? (
                  <p className="text-slate-400 italic">No designs yet. Create your first blueprint!</p>
                ) : (
                  <div className="space-y-4">
                    {history.map(entry => (
                      <div
                        key={entry.id}
                        className="border border-slate-200 rounded-lg p-4 hover:shadow-md transition cursor-pointer"
                        onClick={() => {
                          setCurrentView("blueprint");
                          setDesign(entry.design);
                          setRoneiDesign(entry.roneiDesign || "");
                          setInput(entry.requirements);
                          if (entry.scenario) setScenario(entry.scenario);
                          if (entry.costPerformance) setCostPerformance(entry.costPerformance);
                          if (entry.complianceLevel) setComplianceLevel(entry.complianceLevel);
                          if (entry.reliabilityLevel) setReliabilityLevel(entry.reliabilityLevel);
                          if (entry.strictnessLevel) setStrictnessLevel(entry.strictnessLevel);
                          setAuditStatus(entry.auditStatus || "");
                          setAuditReport(entry.auditReport || "");
                          setSecurityReport(entry.securityReport || "");
                          setCostReport(entry.costReport || "");
                          setReliabilityReport(entry.reliabilityReport || "");
                          setAgentChat(entry.agentChat || "");
                        }}
                      >
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <p className="font-semibold text-slate-800">{entry.requirements.substring(0, 50)}...</p>
                            <p className="text-sm text-slate-500 mt-1">{entry.timestamp}</p>
                          </div>
                          {entry.auditStatus && (
                            <span className={`text-xs font-semibold px-2 py-1 rounded-full ${entry.auditStatus === 'approved' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}`}>
                              {entry.auditStatus.toUpperCase()}
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
            {currentView === "audits" && (
              <div>
                <h2 className="text-2xl font-bold mb-6 text-slate-800">Security Audits</h2>
                {!auditReport && !securityReport && !costReport && !reliabilityReport ? (
                  <p className="text-slate-400 italic">
                    No audit available yet. Generate a blueprint first to see its security review.
                  </p>
                ) : (
                  <>
                    {auditStatus && (
                      <div className="mb-4">
                        <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wide ${auditStatus === 'approved' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}`}>
                          {auditStatus === 'approved' ? 'Approved' : 'Needs Revision'}
                        </span>
                      </div>
                    )}
                    {securityReport && (
                      <div className="mb-6">
                        <h3 className="text-lg font-semibold mb-2 text-slate-800">Security Analyst Report</h3>
                        <div className="prose prose-slate max-w-none">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>{securityReport}</ReactMarkdown>
                        </div>
                      </div>
                    )}
                    {costReport && (
                      <div className="mb-6">
                        <h3 className="text-lg font-semibold mb-2 text-slate-800">Cost Optimization Report</h3>
                        <div className="prose prose-slate max-w-none">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>{costReport}</ReactMarkdown>
                        </div>
                      </div>
                    )}
                    {reliabilityReport && (
                      <div className="mb-6">
                        <h3 className="text-lg font-semibold mb-2 text-slate-800">Reliability & Operations Report</h3>
                        <div className="prose prose-slate max-w-none">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>{reliabilityReport}</ReactMarkdown>
                        </div>
                      </div>
                    )}
                    {auditReport && (
                      <div className="prose prose-slate max-w-none">
                        <h3 className="text-lg font-semibold mb-2 text-slate-800">Chief Auditor Verdict</h3>
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>{auditReport}</ReactMarkdown>
                      </div>
                    )}
                  </>
                )}
              </div>
            )}
            {currentView === "agents" && (
              <div>
                <h2 className="text-2xl font-bold mb-6 text-slate-800">Agent Chat</h2>
                {!agentChat ? (
                  <p className="text-slate-400 italic">
                    No conversation yet. Generate a blueprint to see Carlos and the auditor discuss your design.
                  </p>
                ) : (
                  <AgentChatView transcript={agentChat} />
                )}
              </div>
            )}
            {currentView === "help" && (
              <div>
                <h2 className="text-2xl font-bold mb-6 text-slate-800">How Carlos Works</h2>
                <p className="text-slate-600 mb-6">
                  Carlos is a small team of specialized cloud agents. Each one reviews your design from a different angle
                  before a Chief Auditor gives the final verdict.
                </p>
                <div className="space-y-4">
                  <AgentInfo
                    iconBg="bg-blue-100"
                    labelColor="text-blue-700"
                    icon={<PenTool size={18} />}
                    name="Carlos (Lead Cloud Architect)"
                    description="Drafts the initial end-to-end cloud architecture blueprint based on your requirements and the selected scenario/priorities."
                  />
                  <AgentInfo
                    iconBg="bg-pink-100"
                    labelColor="text-pink-700"
                    icon={<PenTool size={18} />}
                    name="Ronei, the Cat (Rival Architect)"
                    description="Creates a competing modern design favoring containers, Kubernetes, and cutting-edge tech. Challenges Carlos' traditional approach with sass and cat puns."
                  />
                  <AgentInfo
                    iconBg="bg-emerald-100"
                    labelColor="text-emerald-700"
                    icon={<ShieldCheck size={18} />}
                    name="Security Analyst"
                    description="Reviews the design for identity, network, data protection, and incident response. Highlights strengths, risks, and concrete security recommendations."
                  />
                  <AgentInfo
                    iconBg="bg-amber-100"
                    labelColor="text-amber-700"
                    icon={<Layout size={18} />}
                    name="Cost Optimization Specialist"
                    description="Analyzes likely cost drivers, suggests savings (reserved/spot, storage lifecycle), and proposes ways to reduce spend without hurting reliability."
                  />
                  <AgentInfo
                    iconBg="bg-purple-100"
                    labelColor="text-purple-700"
                    icon={<Cloud size={18} />}
                    name="SRE / Reliability Engineer"
                    description="Looks at failure modes, scaling, observability, and runbooks so the system can be operated reliably in production."
                  />
                  <AgentInfo
                    iconBg="bg-slate-100"
                    labelColor="text-slate-700"
                    icon={<MessageCircle size={18} />}
                    name="Chief Architecture Auditor"
                    description="Combines all prior reports and issues the final APPROVED / NEEDS REVISION verdict, with key strengths and required changes before go-live."
                  />
                </div>
                <div className="mt-8 text-sm text-slate-500">
                  Tip: Use the controls above the blueprint editor to choose a scenario and tune cost, compliance, and reliability. All agents will take these into account.
                </div>
              </div>
            )}
            {currentView === "analytics" && (
              <AnalyticsView history={history} />
            )}
          </div>
        </div>

        {/* Input Bar */}
        {currentView === "blueprint" && (
        <div className="p-6 bg-white border-t border-slate-200">
          <div className="max-w-3xl mx-auto relative">
            <input 
              className="w-full p-4 pr-16 border rounded-xl shadow-inner focus:ring-2 focus:ring-blue-500 outline-none"
              placeholder="Tell Carlos what you need to build..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAskCarlos()}
            />
            <button 
              onClick={() => {
                console.log("Button clicked!");
                handleAskCarlos();
              }}
              disabled={isDesigning}
              className="absolute right-2 top-2 p-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-slate-300"
            >
              {isDesigning ? <Loader2 className="animate-spin"/> : <Send size={20}/>}
            </button>
          </div>
        </div>
        )}
      </main>
    </div>
  );
}

function NavItem({ icon, label, active = false, onClick }) {
  return (
    <div 
      onClick={onClick}
      className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition ${active ? 'bg-blue-600' : 'hover:bg-slate-800 text-slate-400'}`}>
      {icon} <span>{label}</span>
    </div>
  );
}

function AgentInfo({ iconBg, labelColor, icon, name, description }) {
  return (
    <div className="flex items-start gap-3 border border-slate-200 rounded-xl p-4 bg-slate-50">
      <div className={`h-10 w-10 rounded-full flex items-center justify-center ${iconBg}`}>
        <span className="text-slate-800">{icon}</span>
      </div>
      <div className="flex-1">
        <div className={`text-xs font-semibold uppercase tracking-wide mb-1 ${labelColor}`}>
          {name}
        </div>
        <p className="text-sm text-slate-700">{description}</p>
      </div>
    </div>
  );
}

function BlueprintWithDiagram({ design }) {
  const { before, diagramDefinition, after } = splitDesignAroundMermaid(design);

  if (!diagramDefinition) {
    return (
      <div className="prose prose-slate max-w-none">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{design}</ReactMarkdown>
      </div>
    );
  }

  return (
    <div className="prose prose-slate max-w-none">
      {before && (
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{before}</ReactMarkdown>
      )}
      <MermaidDiagram definition={diagramDefinition} />
      {after && (
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{after}</ReactMarkdown>
      )}
    </div>
  );
}

function splitDesignAroundMermaid(text) {
  if (!text) return { before: "", diagramDefinition: null, after: "" };

  const regex = /```mermaid\s*([\s\S]*?)```/m;
  const match = text.match(regex);
  if (!match) {
    return { before: text, diagramDefinition: null, after: "" };
  }

  const before = text.slice(0, match.index).trim();
  const diagramDefinition = (match[1] || "").trim();
  const after = text.slice(match.index + match[0].length).trim();
  return { before, diagramDefinition, after };
}

function MermaidDiagram({ definition }) {
  const containerRef = useRef(null);

  useEffect(() => {
    if (!definition || !containerRef.current) return;

    const id = `mermaid-${Math.random().toString(36).slice(2, 9)}`;

    mermaid.initialize({ startOnLoad: false });

    mermaid
      .render(id, definition)
      .then(({ svg }) => {
        if (!containerRef.current) return;

        if (typeof svg === 'string' && svg.includes('Syntax error in text')) {
          console.warn('Mermaid syntax error in diagram definition:', definition);
          containerRef.current.innerHTML =
            '<div class="bg-amber-50 border border-amber-200 rounded p-3"><p class="text-sm text-amber-800 font-medium">⚠️ Diagram Syntax Error</p><p class="text-xs text-amber-700 mt-1">The generated architecture diagram has syntax issues. This doesn\'t affect the blueprint quality - you can still read the detailed design below.</p></div>';
        } else {
          containerRef.current.innerHTML = svg;
        }
      })
      .catch((e) => {
        console.error('Error rendering mermaid diagram', e, '\nDefinition:\n', definition);
        if (containerRef.current) {
          containerRef.current.innerHTML =
            '<div class="bg-red-50 border border-red-200 rounded p-3"><p class="text-sm text-red-800 font-medium">⚠️ Diagram Rendering Error</p><p class="text-xs text-red-700 mt-1">Unable to render the architecture diagram. The detailed blueprint below is still valid.</p></div>';
        }
      });
  }, [definition]);

  return <div ref={containerRef} className="overflow-x-auto" />;
}

function AnalyticsView({ history }) {
  if (!history.length) {
    return (
      <div>
        <h2 className="text-2xl font-bold mb-6 text-slate-800">Analytics</h2>
        <p className="text-slate-400 italic">Generate some blueprints to see analytics.</p>
      </div>
    );
  }

  const total = history.length;
  const approved = history.filter(h => h.auditStatus === 'approved').length;
  const needsRevision = history.filter(h => h.auditStatus && h.auditStatus !== 'approved').length;

  const scenarioCounts = history.reduce((acc, h) => {
    const key = h.scenario || 'custom';
    acc[key] = (acc[key] || 0) + 1;
    return acc;
  }, {});

  const blockers = history
    .filter(h => h.auditStatus && h.auditStatus !== 'approved' && h.auditReport)
    .slice(0, 5)
    .map(h => ({
      id: h.id,
      timestamp: h.timestamp,
      snippet: (h.auditReport.split('\n').find(line => line.trim().startsWith('-')) || h.auditReport).slice(0, 200),
    }));

  const scenarioLabel = (key) => {
    if (key === 'public_web_app') return 'Public Web App';
    if (key === 'data_pipeline') return 'Data Pipeline / Analytics';
    if (key === 'event_driven') return 'Event-driven Microservices';
    return 'Custom';
  };

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6 text-slate-800">Analytics</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="border border-slate-200 rounded-xl p-4 bg-slate-50">
          <div className="text-xs font-semibold uppercase text-slate-500 mb-1">Total Blueprints</div>
          <div className="text-2xl font-bold text-slate-800">{total}</div>
        </div>
        <div className="border border-slate-200 rounded-xl p-4 bg-slate-50">
          <div className="text-xs font-semibold uppercase text-slate-500 mb-1">Approved</div>
          <div className="text-2xl font-bold text-emerald-700">{approved}</div>
        </div>
        <div className="border border-slate-200 rounded-xl p-4 bg-slate-50">
          <div className="text-xs font-semibold uppercase text-slate-500 mb-1">Needs Revision</div>
          <div className="text-2xl font-bold text-amber-700">{needsRevision}</div>
        </div>
      </div>

      <div className="mb-8">
        <h3 className="text-lg font-semibold mb-3 text-slate-800">Scenario Popularity</h3>
        <div className="space-y-2">
          {Object.entries(scenarioCounts).map(([key, count]) => (
            <div key={key} className="flex justify-between text-sm text-slate-700">
              <span>{scenarioLabel(key)}</span>
              <span className="font-semibold">{count}</span>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-3 text-slate-800">Recent Blockers from Auditor</h3>
        {blockers.length === 0 ? (
          <p className="text-slate-400 italic">No blocking issues recorded yet.</p>
        ) : (
          <div className="space-y-3">
            {blockers.map(b => (
              <div key={b.id} className="border border-slate-200 rounded-lg p-3 bg-white">
                <div className="text-xs text-slate-500 mb-1">{b.timestamp}</div>
                <div className="text-sm text-slate-700">{b.snippet}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function AgentChatView({ transcript }) {
  const messages = parseAgentTranscript(transcript);

  if (!messages.length) {
    return (
      <div className="prose prose-slate max-w-none">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{transcript}</ReactMarkdown>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {messages.map((msg, idx) => {
        const { iconBg, labelColor, icon } = getAgentVisuals(msg.agent);
        return (
          <div key={idx} className="flex items-start gap-3">
            <div className={`h-10 w-10 rounded-full flex items-center justify-center ${iconBg}`}>
              <span className="text-slate-800">{icon}</span>
            </div>
            <div className="flex-1">
              <div className={`text-xs font-semibold uppercase tracking-wide mb-1 ${labelColor}`}>
                {msg.agent}
              </div>
              <div className="prose prose-slate max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function parseAgentTranscript(text) {
  if (!text) return [];
  const lines = text.split("\n");
  const messages = [];
  let currentAgent = null;
  let buffer = [];

  const flush = () => {
    if (currentAgent && buffer.length) {
      const content = buffer.join("\n").trim();
      if (content) {
        messages.push({ agent: currentAgent, content });
      }
    }
    buffer = [];
  };

  const headerRegex = /^\*\*(Carlos|Security Analyst|Cost Specialist|SRE|Chief Auditor):\*\*\s*$/;

  for (const line of lines) {
    const match = line.match(headerRegex);
    if (match) {
      flush();
      currentAgent = match[1];
    } else {
      buffer.push(line);
    }
  }

  flush();
  return messages;
}

function getAgentVisuals(agent) {
  const name = agent.toLowerCase();

  if (name.startsWith("carlos")) {
    return {
      iconBg: "bg-blue-100",
      labelColor: "text-blue-700",
      icon: <PenTool size={18} />,
    };
  }

  if (name.startsWith("security")) {
    return {
      iconBg: "bg-emerald-100",
      labelColor: "text-emerald-700",
      icon: <ShieldCheck size={18} />,
    };
  }

  if (name.startsWith("cost")) {
    return {
      iconBg: "bg-amber-100",
      labelColor: "text-amber-700",
      icon: <Layout size={18} />,
    };
  }

  if (name.startsWith("sre")) {
    return {
      iconBg: "bg-purple-100",
      labelColor: "text-purple-700",
      icon: <Cloud size={18} />,
    };
  }

  if (name.includes("auditor")) {
    return {
      iconBg: "bg-slate-100",
      labelColor: "text-slate-700",
      icon: <MessageCircle size={18} />,
    };
  }

  return {
    iconBg: "bg-slate-100",
    labelColor: "text-slate-600",
    icon: <MessageCircle size={18} />,
  };
}
