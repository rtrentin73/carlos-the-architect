import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import mermaid from 'mermaid';
import { Layout, Send, Cloud, ShieldCheck, PenTool, Loader2, MessageCircle, Activity, LogOut, User, Paperclip, X, Copy, Check, Zap, BarChart3, Shield, ChevronDown, ChevronUp, Code, FileCode, Trash2, Clock, Hash } from 'lucide-react';
import Splash from './components/Splash';
import carlosBackground from './assets/splash.jpg';
import LoginPage from './components/LoginPage';
import DeploymentTracker from './components/DeploymentTracker';
import FeedbackDashboard from './components/FeedbackDashboard';
import AdminDashboard from './components/AdminDashboard';
import { useAuth } from './contexts/AuthContext';

export default function App() {
  const { user, token, loading, logout, isAuthenticated } = useAuth();
  const [showSplash, setShowSplash] = useState(true);
  const [input, setInput] = useState("");
  const [scenario, setScenario] = useState("custom");
  const [costPerformance, setCostPerformance] = useState("balanced");
  const [complianceLevel, setComplianceLevel] = useState("standard");
  const [reliabilityLevel, setReliabilityLevel] = useState("normal");
  const [strictnessLevel, setStrictnessLevel] = useState("balanced");
 
  const backendBaseUrl = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

  // File upload state
  const [uploadedFile, setUploadedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef(null);

  const [design, setDesign] = useState("");
  const [roneiDesign, setRoneiDesign] = useState("");
  const [isDesigning, setIsDesigning] = useState(false);
  const [auditStatus, setAuditStatus] = useState("");
  const [auditReport, setAuditReport] = useState("");
  const [securityReport, setSecurityReport] = useState("");
  const [costReport, setCostReport] = useState("");
  const [reliabilityReport, setReliabilityReport] = useState("");
  const [recommendation, setRecommendation] = useState("");
  const [terraformCode, setTerraformCode] = useState("");
  const [terraformValidation, setTerraformValidation] = useState("");
  const [copied, setCopied] = useState(false);
  const [isCacheHit, setIsCacheHit] = useState(false);
  const [agentChat, setAgentChat] = useState("");
  const [lastAgentInChat, setLastAgentInChat] = useState(null); // Track which agent was last added to chat
  const [references, setReferences] = useState([]);
  const [currentView, setCurrentView] = useState("blueprint");
  const [currentDesignId, setCurrentDesignId] = useState(null);
  const [designStartTime, setDesignStartTime] = useState(null);

  // Requirements clarification state
  const [clarificationNeeded, setClarificationNeeded] = useState(false);
  const [clarificationQuestions, setClarificationQuestions] = useState("");
  const [streamingQuestions, setStreamingQuestions] = useState("");
  const [userAnswers, setUserAnswers] = useState("");
  const [originalRequirements, setOriginalRequirements] = useState("");
  const [blueprintTab, setBlueprintTab] = useState("carlos");
  const [history, setHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyPersistent, setHistoryPersistent] = useState(true);
  const [activityLog, setActivityLog] = useState([]);
  const [agentStatuses, setAgentStatuses] = useState({
    design: 'pending',
    ronei_design: 'pending',
    security: 'pending',
    cost: 'pending',
    reliability: 'pending',
    audit: 'pending',
    recommender: 'pending',
    terraform_coder: 'pending',
    terraform_validator: 'pending'
  });
  const [tokenCounts, setTokenCounts] = useState({
    carlos: 0,
    ronei_design: 0,
    terraform_coder: 0,
    requirements_gathering: 0,
    refine_requirements: 0,
    security: 0,
    cost: 0,
    reliability: 0,
    audit: 0,
    recommender: 0
  });

  useEffect(() => {
    const timer = setTimeout(() => setShowSplash(false), 3000);
    return () => clearTimeout(timer);
  }, []);

  // Fetch design history from backend when user is authenticated
  useEffect(() => {
    const fetchHistory = async () => {
      if (!isAuthenticated || !token) return;

      setHistoryLoading(true);
      try {
        console.log("📚 Fetching design history...");
        const response = await fetch(`${backendBaseUrl}/history`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (response.ok) {
          const data = await response.json();
          console.log(`📚 History response: ${data.count} designs, persistent: ${data.persistent}`);
          setHistoryPersistent(data.persistent === true);
          // Transform backend data to match frontend format
          const transformedHistory = (data.designs || []).map(d => ({
            id: d.id,
            requirements: d.requirements || "",
            design: d.architecture || "",
            roneiDesign: d.ronei_design || "",
            scenario: d.scenario || "custom",
            costPerformance: d.cost_performance || "balanced",
            complianceLevel: d.compliance_level || "standard",
            reliabilityLevel: d.reliability_level || "normal",
            strictnessLevel: d.strictness_level || "balanced",
            auditStatus: d.audit_status || "",
            auditReport: d.audit_report || "",
            securityReport: d.security_analysis || "",
            costReport: d.cost_estimate || "",
            reliabilityReport: d.reliability_analysis || "",
            recommendation: d.recommendation || "",
            terraformCode: d.terraform || "",
            terraformValidation: d.terraform_validation || "",
            agentChat: d.agent_chat || "",
            carlosTokens: d.carlos_tokens || 0,
            roneiTokens: d.ronei_tokens || 0,
            totalTokens: d.total_tokens || 0,
            durationSeconds: d.duration_seconds || 0,
            timestamp: d.created_at ? new Date(d.created_at).toLocaleString() : "",
            title: d.title || ""
          }));
          setHistory(transformedHistory);
        } else {
          const errorText = await response.text();
          console.error(`❌ History fetch failed (${response.status}): ${errorText}`);
        }
      } catch (error) {
        console.error("❌ Failed to fetch design history:", error);
      } finally {
        setHistoryLoading(false);
      }
    };

    fetchHistory();
  }, [isAuthenticated, token, backendBaseUrl]);

  const handleStreamEvent = (event) => {
    const agentDescriptions = {
      design: 'Carlos (Lead Cloud Architect) - Designing cloud infrastructure',
      ronei_design: 'Ronei (Rival Architect) - Creating alternative modern design',
      security: 'Security Analyst - Reviewing security posture',
      cost: 'Cost Optimization Specialist - Analyzing cost efficiency',
      reliability: 'SRE - Evaluating reliability and operations',
      audit: 'Chief Auditor - Performing final audit review',
      recommender: 'Design Recommender - Choosing best design approach',
      terraform_coder: 'Terraform Coder - Generating infrastructure-as-code',
      terraform_validator: 'Terraform Validator - Reviewing infrastructure code'
    };

    switch (event.type) {
      case "cache_hit":
        console.log(`📦 Cache HIT - Using cached design pattern`);
        setIsCacheHit(true);
        setActivityLog(prev => [...prev, {
          id: Date.now() + Math.random(),
          type: 'cache',
          agent: 'cache',
          message: '⚡ Using cached design pattern - instant response!',
          timestamp: event.timestamp || new Date().toISOString()
        }]);
        break;

      case "agent_start":
        console.log(`🚀 Agent ${event.agent} started${event.cached ? ' (cached)' : ''}`);
        setActivityLog(prev => [...prev, {
          id: Date.now() + Math.random(),
          type: 'start',
          agent: event.agent,
          message: agentDescriptions[event.agent] || `Agent ${event.agent} started`,
          timestamp: event.timestamp || new Date().toISOString()
        }]);
        setAgentStatuses(prev => ({ ...prev, [event.agent]: 'active' }));

        // Add agent header to agentChat for agents that contribute to conversation
        const agentChatHeaders = {
          carlos: '**Carlos:**\n',
          ronei_design: '**Ronei:**\n',
          security: '**Security Analyst:**\n',
          cost: '**Cost Specialist:**\n',
          reliability: '**SRE:**\n',
          audit: '**Chief Auditor:**\n',
          recommender: '**Design Recommender:**\n',
          terraform_coder: '**Terraform Coder:**\n',
          terraform_validator: '**Terraform Validator:**\n',
          terraform_corrector: '**Terraform Coder (Correction):**\n',
          requirements_gathering: '**Requirements Team:**\n',
          refine_requirements: '**Refined Requirements:**\n',
        };

        if (agentChatHeaders[event.agent]) {
          setAgentChat(prev => prev + agentChatHeaders[event.agent]);
          setLastAgentInChat(event.agent);
        }
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

        // Add trailing newline to agentChat when agent completes
        const chatAgents = [
          'carlos', 'ronei_design', 'security', 'cost', 'reliability', 'audit',
          'recommender', 'terraform_coder', 'terraform_validator', 'terraform_corrector',
          'requirements_gathering', 'refine_requirements'
        ];
        if (chatAgents.includes(event.agent)) {
          setAgentChat(prev => prev + '\n\n');
        }
        break;

      case "token":
        // Map agents to their state setters and display names
        const agentStreamConfig = {
          carlos: { setter: setDesign, name: 'Carlos' },
          ronei_design: { setter: setRoneiDesign, name: 'Ronei' },
          terraform_coder: { setter: setTerraformCode, name: 'Terraform Coder' },
          terraform_validator: { setter: setTerraformValidation, name: 'Terraform Validator' },
          terraform_corrector: { setter: setTerraformCode, name: 'Terraform Corrector' },
          requirements_gathering: { setter: setStreamingQuestions, name: 'Requirements Team' },
          refine_requirements: { setter: null, name: 'Requirements Refiner' }, // Only streams to agentChat
          security: { setter: setSecurityReport, name: 'Security Analyst' },
          cost: { setter: setCostReport, name: 'Cost Specialist' },
          reliability: { setter: setReliabilityReport, name: 'SRE' },
          audit: { setter: setAuditReport, name: 'Chief Auditor' },
          recommender: { setter: setRecommendation, name: 'Design Recommender' }
        };

        // Agents that contribute to the agent chat conversation
        const agentChatAgents = [
          'carlos', 'ronei_design', 'security', 'cost', 'reliability', 'audit',
          'recommender', 'terraform_coder', 'terraform_validator', 'terraform_corrector',
          'requirements_gathering', 'refine_requirements'
        ];

        const config = agentStreamConfig[event.agent];
        if (config) {
          // Update the agent's specific content state
          if (config.setter) {
            config.setter(prev => prev + event.content);
          }

          // Also append to agentChat for conversation view
          if (agentChatAgents.includes(event.agent)) {
            setAgentChat(prev => prev + event.content);
          }

          // Update token count and add activity log entry every 50 tokens
          setTokenCounts(prev => {
            const newCount = (prev[event.agent] || 0) + 1;
            if (newCount % 50 === 0) {
              setActivityLog(activityPrev => [...activityPrev, {
                id: Date.now() + Math.random(),
                type: 'streaming',
                agent: event.agent,
                message: `${config.name} streaming... (${newCount} tokens)`,
                timestamp: event.timestamp || new Date().toISOString()
              }]);
            }
            return { ...prev, [event.agent]: newCount };
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
          recommendation: 'Design Recommendation',
          terraform_code: 'Terraform Infrastructure Code',
          terraform_validation: 'Terraform Validation Report'
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
            setRecommendation(event.content);
            console.log("Recommendation received:", event.content);
            break;
          case "terraform_code":
            setTerraformCode(event.content);
            console.log("Terraform code generated");
            break;
          case "terraform_validation":
            setTerraformValidation(event.content);
            console.log("Terraform validation completed");
            break;
        }
        break;

      case "complete":
        console.log("🎉 Design generation complete!");
        const summary = event.summary;

        // Check if clarification is needed
        if (summary.clarification_needed) {
          console.log("❓ Clarification needed from user");
          setClarificationNeeded(true);
          // Extract just the questions from agent_chat (remove "**Requirements Team:**\n" prefix)
          const questionsText = (summary.agent_chat || "").replace(/^\*\*Requirements Team:\*\*\n?/, '').trim();
          setClarificationQuestions(questionsText);
          setStreamingQuestions(""); // Clear streaming state
          setIsDesigning(false);
          return;
        }

        // Clear clarification state
        setClarificationNeeded(false);
        setClarificationQuestions("");
        setStreamingQuestions("");

        // Generate design ID and save to history
        const designId = `design-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
        setCurrentDesignId(designId);

        // Calculate total tokens and duration
        const totalTokens = Object.values(tokenCounts).reduce((sum, count) => sum + (count || 0), 0);
        const durationSeconds = designStartTime ? Math.round((Date.now() - designStartTime) / 1000) : 0;

        const newEntry = {
          id: designId,
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
          recommendation: summary.recommendation || "",
          terraformCode: summary.terraform_code || "",
          terraformValidation: summary.terraform_validation || "",
          agentChat: summary.agent_chat || "",
          carlosTokens: tokenCounts.carlos,
          roneiTokens: tokenCounts.ronei_design,
          totalTokens,
          durationSeconds,
          timestamp: new Date().toLocaleString()
        };

        // Save to backend API (fire and forget, update local state immediately)
        const updatedHistory = [newEntry, ...history];
        setHistory(updatedHistory);

        // Async save to backend
        console.log(`💾 Saving design ${designId} to backend...`);
        fetch(`${backendBaseUrl}/history`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            id: designId,
            requirements: input,
            scenario,
            cost_performance: costPerformance,
            compliance_level: complianceLevel,
            reliability_level: reliabilityLevel,
            strictness_level: strictnessLevel,
            architecture: summary.design,
            ronei_design: summary.ronei_design || "",
            audit_status: summary.audit_status || "",
            audit_report: summary.audit_report || "",
            security_analysis: summary.security_report || "",
            cost_estimate: summary.cost_report || "",
            reliability_analysis: summary.reliability_report || "",
            recommendation: summary.recommendation || "",
            terraform: summary.terraform_code || "",
            terraform_validation: summary.terraform_validation || "",
            agent_chat: summary.agent_chat || "",
            carlos_tokens: tokenCounts.carlos,
            ronei_tokens: tokenCounts.ronei_design,
            total_tokens: totalTokens,
            duration_seconds: durationSeconds
          })
        }).then(async response => {
          if (response.ok) {
            const data = await response.json();
            console.log(`✅ Design ${designId} saved to backend (persistent: ${data.design?.id ? 'yes' : 'unknown'})`);
          } else {
            const errorText = await response.text();
            console.error(`❌ Failed to save design to backend (${response.status}): ${errorText}`);
          }
        }).catch(error => {
          console.error("❌ Error saving design to backend:", error);
        });
        setAgentChat(summary.agent_chat || "");
        // Set terraform validation from summary (in case streaming was missed)
        if (summary.terraform_validation) {
          setTerraformValidation(summary.terraform_validation);
        }
        // Set references from web search
        if (summary.references && summary.references.length > 0) {
          setReferences(summary.references);
        }
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

  // Delete design from history
  const deleteFromHistory = (entryId, e) => {
    e.stopPropagation(); // Prevent triggering the parent onClick
    if (window.confirm('Are you sure you want to delete this design from history?')) {
      // Update local state immediately
      const updatedHistory = history.filter(entry => entry.id !== entryId);
      setHistory(updatedHistory);

      // Delete from backend
      fetch(`${backendBaseUrl}/history/${entryId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }).then(response => {
        if (!response.ok) {
          console.error("Failed to delete design from backend");
        }
      }).catch(error => {
        console.error("Error deleting design from backend:", error);
      });
    }
  };

  // File upload handlers
  const handleFileUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file size (50MB)
    const maxSize = 50 * 1024 * 1024;
    if (file.size > maxSize) {
      console.error('File too large. Maximum size is 50MB');
      return;
    }

    setUploading(true);
    console.log(`📤 Uploading ${file.name}...`);

    try {
      const formData = new FormData();
      formData.append('file', file);

      // Start async document processing
      const response = await fetch(`${backendBaseUrl}/upload-document`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Upload failed');
      }

      const data = await response.json();
      const taskId = data.task_id;

      console.log(`⏳ Processing ${file.name}...`);

      // Poll for completion
      const pollInterval = 2000;
      const maxAttempts = 60;
      let attempts = 0;

      const checkStatus = async () => {
        try {
          const statusResponse = await fetch(`${backendBaseUrl}/documents/${taskId}`, {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          });

          if (!statusResponse.ok) {
            throw new Error('Failed to check document status');
          }

          const statusData = await statusResponse.json();

          if (statusData.status === 'completed') {
            // Ensure extracted_text is a string (prevent null/undefined from crashing React)
            const extractedText = statusData.extracted_text || '';

            if (!extractedText) {
              console.error(`❌ Document ${file.name} completed but no text was extracted`);
              setUploading(false);
              return;
            }

            // Merge extracted text with existing input
            const mergedText = input.trim()
              ? `${input.trim()}\n\n${extractedText}`
              : extractedText;

            setInput(mergedText);
            setUploadedFile({ name: file.name, message: `✅ ${file.name} processed` });

            console.log(`✅ ${file.name} processed successfully`);
            setUploading(false);

            setTimeout(() => setUploadedFile(null), 5000);

          } else if (statusData.status === 'failed') {
            console.error(`❌ Failed to process ${file.name}: ${statusData.error}`);
            setUploading(false);

          } else {
            attempts++;
            if (attempts < maxAttempts) {
              setTimeout(checkStatus, pollInterval);
            } else {
              console.error(`❌ Document processing timeout`);
              setUploading(false);
            }
          }

        } catch (error) {
          console.error(`❌ Status check failed: ${error.message}`);
          setUploading(false);
        }
      };

      checkStatus();

    } catch (error) {
      console.error(`❌ Upload failed: ${error.message}`);
      setUploading(false);
    } finally {
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleFileButtonClick = () => {
    fileInputRef.current?.click();
  };

  const removeUploadedFile = () => {
    setUploadedFile(null);
  };

  const submitAnswers = async () => {
    if (!userAnswers.trim()) return;

    setClarificationNeeded(false);
    await handleAskCarlos(userAnswers);
    setUserAnswers(""); // Clear answers after submission
  };

  const handleAskCarlos = async (providedAnswers = null) => {
    // Reset all state (but preserve original requirements if answering clarification)
    setDesign("");
    setRoneiDesign("");
    setSecurityReport("");
    setCostReport("");
    setReliabilityReport("");
    setAuditReport("");
    setAuditStatus("");
    setRecommendation("");
    setTerraformCode("");
    setTerraformValidation("");
    setAgentChat("");
    setLastAgentInChat(null);
    setReferences([]);
    setStreamingQuestions("");
    setActivityLog([]);
    setIsCacheHit(false);
    setCurrentDesignId(null); // Reset design ID for new design
    setAgentStatuses({
      design: 'pending',
      ronei_design: 'pending',
      security: 'pending',
      cost: 'pending',
      reliability: 'pending',
      audit: 'pending',
      recommender: 'pending',
      terraform_coder: 'pending',
      terraform_validator: 'pending'
    });
    setTokenCounts({
      carlos: 0,
      ronei_design: 0,
      terraform_coder: 0,
      requirements_gathering: 0,
      refine_requirements: 0,
      security: 0,
      cost: 0,
      reliability: 0,
      audit: 0,
      recommender: 0
    });
    setIsDesigning(true);
    setDesignStartTime(Date.now());

    // Save original requirements on first call
    if (!providedAnswers) {
      setOriginalRequirements(input);
    }

    console.log("=== Starting streaming design request ===");
    console.log("Input:", providedAnswers ? originalRequirements : input);
    if (providedAnswers) {
      console.log("User answers:", providedAnswers);
    }

    // Build request body
    const requestBody = {
      text: providedAnswers ? originalRequirements : input,
      scenario,
      priorities: {
        cost_performance: costPerformance,
        compliance: complianceLevel,
        reliability: reliabilityLevel,
        strictness: strictnessLevel,
      },
    };

    if (providedAnswers) {
      requestBody.user_answers = providedAnswers;
    }

    try {
      console.log(`Streaming from ${backendBaseUrl}/design-stream`);
      const response = await fetch(`${backendBaseUrl}/design-stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify(requestBody),
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
      "## Design Recommendation",
      "",
      recommendation || "_No recommendation generated._",
      "",
      "## Terraform Infrastructure Code",
      "",
      terraformCode || "_No Terraform code generated._",
      "",
      "## Terraform Validation Report",
      "",
      terraformValidation || "_No validation report generated._",
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

  // Show loading while checking auth
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-400" />
      </div>
    );
  }

  // Show login if not authenticated
  if (!isAuthenticated) {
    return <LoginPage />;
  }

  if (showSplash) return <Splash />;

  return (
    <div className="flex h-screen bg-slate-50">
      {/* Sidebar Navigation */}
      <aside className="w-64 bg-slate-900 text-white p-6 flex flex-col">
        <div className="flex items-center gap-3 mb-10">
          <div className="bg-blue-500 p-2 rounded-lg"><Layout size={20}/></div>
          <span className="font-bold text-xl text-white whitespace-nowrap">Carlos AI</span>
        </div>
        <nav className="space-y-4 flex-1">
          <NavItem icon={<PenTool size={18}/>} label="New Blueprint" active={currentView === "blueprint"} onClick={() => setCurrentView("blueprint")} />
          <NavItem icon={<Activity size={18}/>} label="Live Activity" active={currentView === "activity"} onClick={() => setCurrentView("activity")} />
          <NavItem icon={<Cloud size={18}/>} label="Cloud History" active={currentView === "history"} onClick={() => setCurrentView("history")} />
          <NavItem icon={<ShieldCheck size={18}/>} label="Security Audits" active={currentView === "audits"} onClick={() => setCurrentView("audits")} />
          <NavItem icon={<MessageCircle size={18}/>} label="Agent Chat" active={currentView === "agents"} onClick={() => setCurrentView("agents")} />
          <NavItem icon={<Layout size={18}/>} label="Help & Agents" active={currentView === "help"} onClick={() => setCurrentView("help")} />
          <NavItem icon={<Cloud size={18}/>} label="Analytics" active={currentView === "analytics"} onClick={() => setCurrentView("analytics")} />
          <NavItem icon={<BarChart3 size={18}/>} label="Feedback" active={currentView === "feedback"} onClick={() => setCurrentView("feedback")} />
          {user?.is_admin && (
            <NavItem icon={<Shield size={18}/>} label="Admin" active={currentView === "admin"} onClick={() => setCurrentView("admin")} />
          )}
        </nav>

        {/* User info and logout */}
        <div className="mt-auto pt-6 border-t border-slate-700">
          <div className="flex items-center gap-3 px-3 py-2 text-slate-300">
            <User size={18} />
            <span className="text-sm truncate">{user?.username}</span>
          </div>
          <button
            onClick={logout}
            className="flex items-center gap-3 w-full p-3 rounded-lg text-slate-400 hover:bg-slate-800 hover:text-white transition"
          >
            <LogOut size={18} />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main Design Area */}
      <main className="flex-1 flex flex-col relative">
        {/* Tiled Carlos background pattern */}
        <div
          className="absolute inset-0 opacity-[0.04] pointer-events-none"
          style={{
            backgroundImage: `url(${carlosBackground})`,
            backgroundSize: '80px 80px',
            backgroundRepeat: 'repeat',
          }}
        />
        <div className="flex-1 overflow-y-auto p-12 relative z-10">
          <div className="max-w-3xl mx-auto bg-white shadow-xl rounded-2xl p-10 min-h-[80vh] border border-slate-200">
            {currentView === "blueprint" && (
              <>
                {/* Show clarification form when needed */}
                {clarificationNeeded ? (
                  <ClarificationForm
                    questions={clarificationQuestions}
                    userAnswers={userAnswers}
                    setUserAnswers={setUserAnswers}
                    onSubmit={submitAnswers}
                    loading={isDesigning}
                  />
                ) : streamingQuestions && isDesigning ? (
                  /* Show streaming questions while Requirements Team is working */
                  <StreamingQuestionsView questions={streamingQuestions} />
                ) : (
                  /* Normal blueprint view */
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
                    <div className="flex border-b border-slate-200 mb-6 overflow-x-auto">
                      <button
                        onClick={() => setBlueprintTab("carlos")}
                        className={`px-4 py-2 font-medium text-sm whitespace-nowrap ${
                          blueprintTab === "carlos"
                            ? "border-b-2 border-blue-500 text-blue-600"
                            : "text-slate-500 hover:text-slate-700"
                        }`}
                      >
                        Carlos' Design
                      </button>
                      <button
                        onClick={() => setBlueprintTab("ronei")}
                        className={`px-4 py-2 font-medium text-sm whitespace-nowrap ${
                          blueprintTab === "ronei"
                            ? "border-b-2 border-purple-500 text-purple-600"
                            : "text-slate-500 hover:text-slate-700"
                        }`}
                      >
                        Ronei's Design
                      </button>
                      {recommendation && (
                        <button
                          onClick={() => setBlueprintTab("recommendation")}
                          className={`px-4 py-2 font-medium text-sm whitespace-nowrap ${
                            blueprintTab === "recommendation"
                              ? "border-b-2 border-indigo-500 text-indigo-600"
                              : "text-slate-500 hover:text-slate-700"
                          }`}
                        >
                          Recommendation
                        </button>
                      )}
                      {terraformCode && (
                        <button
                          onClick={() => setBlueprintTab("terraform")}
                          className={`px-4 py-2 font-medium text-sm whitespace-nowrap ${
                            blueprintTab === "terraform"
                              ? "border-b-2 border-green-500 text-green-600"
                              : "text-slate-500 hover:text-slate-700"
                          }`}
                        >
                          Terraform Code
                        </button>
                      )}
                      {terraformValidation && (
                        <button
                          onClick={() => setBlueprintTab("validation")}
                          className={`px-4 py-2 font-medium text-sm whitespace-nowrap ${
                            blueprintTab === "validation"
                              ? "border-b-2 border-orange-500 text-orange-600"
                              : "text-slate-500 hover:text-slate-700"
                          }`}
                        >
                          Validation
                        </button>
                      )}
                      {references.length > 0 && (
                        <button
                          onClick={() => setBlueprintTab("references")}
                          className={`px-4 py-2 font-medium text-sm whitespace-nowrap ${
                            blueprintTab === "references"
                              ? "border-b-2 border-cyan-500 text-cyan-600"
                              : "text-slate-500 hover:text-slate-700"
                          }`}
                        >
                          References ({references.length})
                        </button>
                      )}
                    </div>

                    {/* Design Content */}
                    {blueprintTab === "carlos" && design && (
                      <BlueprintWithDiagram design={design} />
                    )}
                    {blueprintTab === "ronei" && roneiDesign && (
                      <BlueprintWithDiagram design={roneiDesign} />
                    )}
                    {blueprintTab === "recommendation" && recommendation && (
                      <div className="prose prose-slate max-w-none">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>{recommendation}</ReactMarkdown>
                      </div>
                    )}
                    {blueprintTab === "terraform" && terraformCode && (
                      <TerraformCodeView
                        code={terraformCode}
                        copied={copied}
                        onCopy={() => {
                          // Extract raw code blocks from markdown
                          const codeBlockRegex = /```(?:hcl|terraform)?\n([\s\S]*?)```/g;
                          const matches = [...terraformCode.matchAll(codeBlockRegex)];
                          const rawCode = matches.length > 0
                            ? matches.map(m => m[1].trim()).join('\n\n')
                            : terraformCode;
                          navigator.clipboard.writeText(rawCode);
                          setCopied(true);
                          setTimeout(() => setCopied(false), 2000);
                        }}
                      />
                    )}
                    {blueprintTab === "validation" && terraformValidation && (
                      <div className="prose prose-slate max-w-none">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>{terraformValidation}</ReactMarkdown>
                      </div>
                    )}
                    {blueprintTab === "references" && references.length > 0 && (
                      <ReferencesSection references={references} />
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

                    {/* Deployment Feedback Tracker */}
                    {!isDesigning && currentDesignId && (design || roneiDesign) && (
                      <div className="mt-8 pt-8 border-t border-slate-200">
                        <DeploymentTracker
                          designId={currentDesignId}
                          requirements={input}
                        />
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
              </>
            )}
            {currentView === "activity" && (
              <div>
                <h2 className="text-2xl font-bold mb-6 text-slate-800 flex items-center gap-2">
                  <Activity size={24} className="text-blue-600" />
                  Live Activity Monitor
                </h2>

                {/* Cache Hit Indicator */}
                {isCacheHit && (
                  <div className="mb-6 p-4 bg-gradient-to-r from-amber-50 to-yellow-50 border border-amber-200 rounded-lg flex items-center gap-3">
                    <div className="p-2 bg-amber-100 rounded-full">
                      <Zap size={20} className="text-amber-600" />
                    </div>
                    <div>
                      <p className="font-semibold text-amber-800">⚡ Instant Response - Cache Hit!</p>
                      <p className="text-sm text-amber-600">This design pattern was cached. Response time: &lt;1 second</p>
                    </div>
                  </div>
                )}

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
                            log.type === 'cache' ? 'bg-amber-50 border-l-4 border-amber-500' :
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
                {!historyPersistent && (
                  <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                    <p className="text-sm text-amber-800">
                      <strong>⚠️ Note:</strong> Design history is stored in memory. Data will be lost when the server restarts. Configure Cosmos DB for persistent storage.
                    </p>
                  </div>
                )}
                {historyLoading ? (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="h-8 w-8 animate-spin text-blue-400" />
                    <span className="ml-3 text-slate-500">Loading history...</span>
                  </div>
                ) : history.length === 0 ? (
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
                          setRecommendation(entry.recommendation || "");
                          setTerraformCode(entry.terraformCode || "");
                          setTerraformValidation(entry.terraformValidation || "");
                          setAgentChat(entry.agentChat || "");
                        }}
                      >
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <p className="font-semibold text-slate-800">{entry.requirements.substring(0, 50)}...</p>
                            <div className="flex items-center gap-4 mt-1">
                              <p className="text-sm text-slate-500">{entry.timestamp}</p>
                              <div className="flex items-center gap-3 text-xs">
                                {entry.totalTokens > 0 && (
                                  <span className="flex items-center gap-1 bg-purple-50 text-purple-600 px-2 py-0.5 rounded" title="Total tokens consumed">
                                    <Hash size={12} />
                                    {entry.totalTokens.toLocaleString()} tokens
                                  </span>
                                )}
                                {entry.durationSeconds > 0 && (
                                  <span className="flex items-center gap-1 bg-slate-100 text-slate-600 px-2 py-0.5 rounded" title="Design generation time">
                                    <Clock size={12} />
                                    {entry.durationSeconds >= 60
                                      ? `${Math.floor(entry.durationSeconds / 60)}m ${entry.durationSeconds % 60}s`
                                      : `${entry.durationSeconds}s`
                                    }
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center gap-2 ml-4">
                            {entry.auditStatus && (
                              <span className={`text-xs font-semibold px-2 py-1 rounded-full ${entry.auditStatus === 'approved' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}`}>
                                {entry.auditStatus.toUpperCase()}
                              </span>
                            )}
                            <button
                              onClick={(e) => deleteFromHistory(entry.id, e)}
                              className="p-1.5 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded transition"
                              title="Delete from history"
                            >
                              <Trash2 size={16} />
                            </button>
                          </div>
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
                  Carlos is a team of specialized cloud agents working together. Two competing architects (Carlos and Ronei)
                  draft designs in parallel, then specialist reviewers analyze both approaches before a final recommendation is made.
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
                  <AgentInfo
                    iconBg="bg-indigo-100"
                    labelColor="text-indigo-700"
                    icon={<Layout size={18} />}
                    name="Design Recommender"
                    description="Analyzes both Carlos' and Ronei's designs along with all specialist reports, then recommends which approach best fits your requirements. Provides detailed tradeoff analysis and explains when you might choose the alternative."
                  />
                  <AgentInfo
                    iconBg="bg-green-100"
                    labelColor="text-green-700"
                    icon={<Cloud size={18} />}
                    name="Terraform Coder"
                    description="Generates production-ready Terraform infrastructure-as-code for the recommended design. Creates modular HCL code with main.tf, variables.tf, outputs.tf, and versions.tf files, following IaC best practices."
                  />
                  <AgentInfo
                    iconBg="bg-orange-100"
                    labelColor="text-orange-700"
                    icon={<ShieldCheck size={18} />}
                    name="Terraform Validator"
                    description="Reviews the generated Terraform code for syntax, security issues, best practices, and completeness. Identifies hardcoded secrets, overly permissive rules, and cloud-specific anti-patterns before deployment."
                  />
                </div>
                <div className="mt-8 p-4 bg-blue-50 rounded-lg border border-blue-200">
                  <p className="text-sm text-blue-800 font-semibold mb-2">⚡ Parallel Execution</p>
                  <p className="text-sm text-blue-700">
                    Carlos and Ronei work simultaneously to draft their designs, cutting total execution time in half!
                    Once both complete, specialist reviewers analyze the approaches sequentially.
                  </p>
                </div>
                <div className="mt-4 text-sm text-slate-500">
                  Tip: Use the controls above the blueprint editor to choose a scenario and tune cost, compliance, and reliability. All agents will take these into account.
                </div>
              </div>
            )}
            {currentView === "analytics" && (
              <AnalyticsView history={history} />
            )}
            {currentView === "feedback" && (
              <FeedbackDashboard />
            )}
            {currentView === "admin" && (
              <AdminDashboard />
            )}
          </div>
        </div>

        {/* Input Bar - hide when showing clarification form */}
        {currentView === "blueprint" && !clarificationNeeded && (
        <div className="p-6 bg-white border-t border-slate-200">
          <div className="max-w-3xl mx-auto">
            {/* File upload confirmation */}
            {uploadedFile && (
              <div className="mb-3 flex items-center gap-2 text-green-600 bg-green-50 px-3 py-2 rounded-lg">
                <span className="text-sm font-medium">{uploadedFile.message}</span>
                <button
                  className="ml-auto hover:text-green-800"
                  onClick={removeUploadedFile}
                >
                  <X size={16} />
                </button>
              </div>
            )}
            <div className="flex gap-3">
              {/* Hidden file input */}
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx,.doc,.txt,.md,.xlsx,.xls,.png,.jpg,.jpeg,.gif,.bmp,.tiff,.tif,.webp"
                onChange={handleFileUpload}
                className="hidden"
              />

              {/* Paperclip button */}
              <button
                onClick={handleFileButtonClick}
                disabled={isDesigning || uploading}
                className="p-4 bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-xl transition-all disabled:opacity-30 disabled:cursor-not-allowed border border-slate-200"
                title="Upload requirements document or image (PDF, DOCX, TXT, MD, XLSX, PNG, JPG - max 50MB)"
              >
                {uploading ? (
                  <Loader2 className="animate-spin" size={20} />
                ) : (
                  <Paperclip size={20} />
                )}
              </button>

              {/* Text input */}
              <input
                className="flex-1 p-4 border rounded-xl shadow-inner focus:ring-2 focus:ring-blue-500 outline-none"
                placeholder="Tell Carlos what you need to build..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleAskCarlos()}
                disabled={isDesigning}
              />

              {/* Send button */}
              <button
                onClick={() => {
                  console.log("Button clicked!");
                  handleAskCarlos();
                }}
                disabled={isDesigning || !input.trim()}
                className="p-4 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-all"
              >
                {isDesigning ? <Loader2 className="animate-spin" size={20}/> : <Send size={20}/>}
              </button>
            </div>
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

    // Professional Mermaid theme configuration
    mermaid.initialize({
      startOnLoad: false,
      theme: 'base',
      themeVariables: {
        // Primary colors - modern blue palette
        primaryColor: '#3b82f6',
        primaryTextColor: '#ffffff',
        primaryBorderColor: '#2563eb',
        // Secondary colors
        secondaryColor: '#e0e7ff',
        secondaryTextColor: '#1e40af',
        secondaryBorderColor: '#6366f1',
        // Tertiary colors
        tertiaryColor: '#f0fdf4',
        tertiaryTextColor: '#166534',
        tertiaryBorderColor: '#22c55e',
        // Background and lines
        background: '#ffffff',
        mainBkg: '#f8fafc',
        lineColor: '#64748b',
        // Node colors
        nodeBorder: '#334155',
        clusterBkg: '#f1f5f9',
        clusterBorder: '#cbd5e1',
        // Text
        titleColor: '#0f172a',
        textColor: '#334155',
        // Flowchart specific
        edgeLabelBackground: '#ffffff',
        // Fonts
        fontFamily: 'ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      },
      flowchart: {
        htmlLabels: true,
        curve: 'basis',
        padding: 20,
        nodeSpacing: 50,
        rankSpacing: 70,
        useMaxWidth: true,
      },
      sequence: {
        diagramMarginX: 20,
        diagramMarginY: 20,
        actorMargin: 80,
        boxMargin: 10,
        boxTextMargin: 10,
        noteMargin: 15,
        messageMargin: 45,
        useMaxWidth: true,
      },
    });

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

  return (
    <div className="bg-gradient-to-br from-slate-50 to-blue-50 border border-slate-200 rounded-xl p-6 shadow-sm">
      <div className="flex items-center gap-2 mb-4">
        <div className="h-8 w-8 rounded-lg bg-blue-100 flex items-center justify-center">
          <Layout size={18} className="text-blue-600" />
        </div>
        <h3 className="font-semibold text-slate-700">Architecture Diagram</h3>
      </div>
      <div ref={containerRef} className="overflow-x-auto bg-white rounded-lg p-4 border border-slate-100" />
    </div>
  );
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
  const [expandedMessages, setExpandedMessages] = useState({});

  const toggleExpand = (idx) => {
    setExpandedMessages(prev => ({
      ...prev,
      [idx]: !prev[idx]
    }));
  };

  // Get preview text (first ~150 chars or 3 lines, whichever is shorter)
  const getPreview = (content) => {
    const lines = content.split('\n').slice(0, 3);
    const preview = lines.join('\n');
    if (preview.length > 150) {
      return preview.substring(0, 150) + '...';
    }
    if (content.length > preview.length) {
      return preview + '...';
    }
    return content;
  };

  // Check if content needs expansion (more than 150 chars or more than 3 lines)
  const needsExpansion = (content) => {
    return content.length > 150 || content.split('\n').length > 3;
  };

  if (!messages.length) {
    return (
      <div className="prose prose-slate max-w-none">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{transcript}</ReactMarkdown>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {messages.map((msg, idx) => {
        const { iconBg, labelColor, icon } = getAgentVisuals(msg.agent);
        const isExpanded = expandedMessages[idx];
        const canExpand = needsExpansion(msg.content);
        const displayContent = isExpanded || !canExpand ? msg.content : getPreview(msg.content);

        return (
          <div
            key={idx}
            className={`flex items-start gap-3 p-3 rounded-lg transition-all ${
              canExpand ? 'cursor-pointer hover:bg-slate-50' : ''
            } ${isExpanded ? 'bg-slate-50 border border-slate-200' : ''}`}
            onClick={() => canExpand && toggleExpand(idx)}
          >
            <div className={`h-10 w-10 rounded-full flex items-center justify-center flex-shrink-0 ${iconBg}`}>
              <span className="text-slate-800">{icon}</span>
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between mb-1">
                <div className={`text-xs font-semibold uppercase tracking-wide ${labelColor}`}>
                  {msg.agent}
                </div>
                {canExpand && (
                  <div className={`flex items-center gap-1 text-xs ${labelColor}`}>
                    {isExpanded ? (
                      <>
                        <span className="text-slate-500">Click to collapse</span>
                        <ChevronUp size={14} />
                      </>
                    ) : (
                      <>
                        <span className="text-slate-500">Click to expand</span>
                        <ChevronDown size={14} />
                      </>
                    )}
                  </div>
                )}
              </div>
              <div className={`prose prose-slate max-w-none ${!isExpanded && canExpand ? 'line-clamp-3' : ''}`}>
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{displayContent}</ReactMarkdown>
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

  // Extended regex to match all agent headers
  // Handles variations like "Terraform Coder (Correction 1):"
  const headerRegex = /^\*\*(Carlos|Security Analyst|Cost Specialist|SRE|Chief Auditor|Ronei|Requirements Team|Refined Requirements|Design Recommender|Terraform Coder|Terraform Coder \(Correction \d+\)|Terraform Validator|Terraform Corrector):\*\*\s*$/i;

  for (const line of lines) {
    const match = line.match(headerRegex);
    if (match) {
      flush();
      // Normalize agent name (remove correction iteration for display)
      let agentName = match[1];
      if (agentName.toLowerCase().startsWith('terraform coder (correction')) {
        agentName = 'Terraform Coder (Correction)';
      }
      currentAgent = agentName;
    } else {
      buffer.push(line);
    }
  }

  flush();
  return messages;
}

function getAgentVisuals(agent) {
  const name = agent.toLowerCase();

  if (name === "cache") {
    return {
      iconBg: "bg-amber-100",
      labelColor: "text-amber-700",
      icon: <Zap size={18} />,
    };
  }

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

  // Ronei - Product Manager / Requirements Analyst
  if (name === "ronei" || name.includes("requirements team") || name.includes("refined requirements")) {
    return {
      iconBg: "bg-indigo-100",
      labelColor: "text-indigo-700",
      icon: <User size={18} />,
    };
  }

  // Design Recommender
  if (name.includes("design recommender")) {
    return {
      iconBg: "bg-cyan-100",
      labelColor: "text-cyan-700",
      icon: <BarChart3 size={18} />,
    };
  }

  // Terraform Coder
  if (name.includes("terraform coder")) {
    return {
      iconBg: "bg-violet-100",
      labelColor: "text-violet-700",
      icon: <Code size={18} />,
    };
  }

  // Terraform Validator
  if (name.includes("terraform validator")) {
    return {
      iconBg: "bg-teal-100",
      labelColor: "text-teal-700",
      icon: <Shield size={18} />,
    };
  }

  // Terraform Corrector
  if (name.includes("terraform corrector")) {
    return {
      iconBg: "bg-orange-100",
      labelColor: "text-orange-700",
      icon: <FileCode size={18} />,
    };
  }

  return {
    iconBg: "bg-slate-100",
    labelColor: "text-slate-600",
    icon: <MessageCircle size={18} />,
  };
}

// Component to display Terraform code with copy button
function TerraformCodeView({ code, copied, onCopy }) {
  return (
    <div className="relative">
      {/* Copy button */}
      <div className="absolute top-0 right-0 z-10">
        <button
          onClick={onCopy}
          className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
            copied
              ? 'bg-green-100 text-green-700 border border-green-300'
              : 'bg-slate-100 text-slate-700 hover:bg-slate-200 border border-slate-300'
          }`}
        >
          {copied ? (
            <>
              <Check size={16} />
              Copied!
            </>
          ) : (
            <>
              <Copy size={16} />
              Copy Code
            </>
          )}
        </button>
      </div>

      {/* Code display */}
      <div className="prose prose-slate max-w-none pt-12">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{code}</ReactMarkdown>
      </div>
    </div>
  );
}

// Component to show streaming questions from Requirements Team
function StreamingQuestionsView({ questions }) {
  return (
    <div className="space-y-6">
      <div className="bg-amber-50 border-l-4 border-amber-500 p-6 rounded-r-lg">
        <div className="flex items-start gap-3">
          <div className="text-3xl animate-pulse">🤔</div>
          <div>
            <h3 className="font-bold text-amber-900 text-xl mb-2">Requirements Team is Analyzing...</h3>
            <p className="text-amber-700 text-sm">
              Carlos and Ronei are reviewing your requirements and preparing clarifying questions.
            </p>
          </div>
        </div>
      </div>

      <div className="bg-gray-50 p-6 rounded-lg border border-gray-200 min-h-[200px]">
        <div className="prose prose-slate max-w-none">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{questions}</ReactMarkdown>
        </div>
        <span className="inline-block w-2 h-5 bg-blue-500 animate-pulse ml-1" />
      </div>
    </div>
  );
}

// References Section Component
function ReferencesSection({ references }) {
  // Group references by source
  const groupedRefs = references.reduce((acc, ref) => {
    const source = ref.source || 'Other';
    if (!acc[source]) acc[source] = [];
    acc[source].push(ref);
    return acc;
  }, {});

  const sourceIcons = {
    'AWS Docs': '🔶',
    'Azure Docs': '🔷',
    'Google Cloud Docs': '🔴',
    'GitHub': '⚫',
    'Medium': '📝',
    'Dev.to': '💻',
    'Stack Overflow': '📚',
    'HashiCorp': '🟣',
    'Kubernetes Docs': '☸️',
    'Serverless Land': '⚡',
    'Article': '📄',
  };

  return (
    <div className="space-y-6">
      <div className="bg-cyan-50 border-l-4 border-cyan-500 p-4 rounded-r-lg">
        <div className="flex items-start gap-3">
          <span className="text-2xl">📚</span>
          <div>
            <h3 className="font-bold text-cyan-900 text-lg">Reference Materials</h3>
            <p className="text-cyan-700 text-sm mt-1">
              These documentation and best practices were consulted during the design process.
            </p>
          </div>
        </div>
      </div>

      {Object.entries(groupedRefs).map(([source, refs]) => (
        <div key={source} className="space-y-3">
          <h4 className="font-semibold text-slate-800 flex items-center gap-2">
            <span>{sourceIcons[source] || '📄'}</span>
            {source}
          </h4>
          <div className="space-y-3 pl-6">
            {refs.map((ref, idx) => (
              <div key={idx} className="border border-slate-200 rounded-lg p-4 bg-white hover:shadow-md transition">
                <a
                  href={ref.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800 font-medium hover:underline"
                >
                  {ref.title}
                </a>
                {ref.snippet && (
                  <p className="text-sm text-slate-600 mt-2 line-clamp-3">
                    {ref.snippet}
                  </p>
                )}
                <p className="text-xs text-slate-400 mt-2 truncate">
                  {ref.url}
                </p>
              </div>
            ))}
          </div>
        </div>
      ))}

      <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 mt-6">
        <p className="text-sm text-slate-600">
          <strong>💡 Tip:</strong> These references were automatically found based on your requirements.
          Check the design document for a "References" section where Carlos and Ronei cite how they used these sources.
        </p>
      </div>
    </div>
  );
}

// Clarification Form Component
function ClarificationForm({ questions, userAnswers, setUserAnswers, onSubmit, loading }) {
  return (
    <div className="space-y-6">
      <div className="bg-blue-50 border-l-4 border-blue-500 p-6 rounded-r-lg">
        <div className="flex items-start gap-3">
          <div className="text-3xl">💬</div>
          <div>
            <h3 className="font-bold text-blue-900 text-xl mb-2">Carlos and Ronei Need More Information</h3>
            <p className="text-blue-700 text-sm">
              Please answer the questions below to help them create better architecture designs for you.
            </p>
          </div>
        </div>
      </div>

      <div className="bg-gray-50 p-6 rounded-lg border border-gray-200">
        <div className="prose prose-slate max-w-none">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{questions}</ReactMarkdown>
        </div>
      </div>

      <div>
        <label className="block text-sm font-semibold text-gray-700 mb-3">
          Your Answers
        </label>
        <textarea
          value={userAnswers}
          onChange={(e) => setUserAnswers(e.target.value)}
          placeholder="Please provide answers to the questions above. Be as specific as possible..."
          className="w-full h-64 p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none resize-y"
          disabled={loading}
        />
      </div>

      <div className="flex justify-end gap-3">
        <button
          onClick={onSubmit}
          disabled={!userAnswers.trim() || loading}
          className="bg-blue-600 text-white px-8 py-3 rounded-lg font-bold hover:bg-blue-700 active:scale-95 transition-all disabled:opacity-30 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {loading ? (
            <>
              <Loader2 className="animate-spin" size={18} />
              Processing...
            </>
          ) : (
            'Submit Answers & Continue'
          )}
        </button>
      </div>
    </div>
  );
}
