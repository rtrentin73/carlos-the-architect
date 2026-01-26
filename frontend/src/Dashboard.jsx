import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { Cloud, ShieldCheck, PenTool, Loader2, Terminal, Paperclip, X } from 'lucide-react';
import carlosImg from './assets/splash.jpg';

export default function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [input, setInput] = useState("");
  const [designDoc, setDesignDoc] = useState("");
  const [status, setStatus] = useState("idle"); // idle, designing, auditing, error
  const [debugLog, setDebugLog] = useState([]);
  const [showDebug, setShowDebug] = useState(true);

  // Requirements clarification state
  const [clarificationNeeded, setClarificationNeeded] = useState(false);
  const [clarificationQuestions, setClarificationQuestions] = useState("");
  const [streamingQuestions, setStreamingQuestions] = useState(""); // For live streaming of questions
  const [userAnswers, setUserAnswers] = useState("");
  const [originalRequirements, setOriginalRequirements] = useState("");

  // File upload state
  const [uploadedFile, setUploadedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef(null);

  const backendBaseUrl = import.meta.env.VITE_BACKEND_URL || "http://localhost:8001";

  // Splash screen effect
  useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 3000);
    return () => clearTimeout(timer);
  }, []);

  // Utility to handle debug logging
  const addLog = (type, message, data = null) => {
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = { timestamp, type, message, data };
    console.log(`[${timestamp}] ${type}:`, message, data || '');
    setDebugLog(prev => [...prev, logEntry]);
  };

  const runCarlos = async (providedAnswers = null) => {
    if (!input.trim() && !providedAnswers) return;

    setDesignDoc("");
    setStreamingQuestions(""); // Reset streaming questions
    if (!providedAnswers) {
      setDebugLog([]);
      setOriginalRequirements(input);
    }
    setStatus("designing");

    // Build request body
    const requestBody = { text: input };
    if (providedAnswers) {
      requestBody.user_answers = providedAnswers;
      addLog('INFO', '📤 Sending answers to Carlos and Ronei...', { answers: providedAnswers });
    } else {
      addLog('INFO', '📤 Sending request to Carlos...', { requirements: input });
    }

    try {
      const response = await fetch(`${backendBaseUrl}/design-stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let chunkCount = 0;
      let carlosDesign = "";
      let roneiDesign = "";

      addLog('INFO', '🔄 Connection established. Streaming design...');

      while (true) {
        const { value, done } = await reader.read();
        if (done) {
          addLog('SUCCESS', '✅ Design finalized', { totalChunks: chunkCount });
          break;
        }

        chunkCount++;
        const chunk = decoder.decode(value);
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const jsonStr = line.replace("data: ", "");
              if (!jsonStr.trim()) continue;

              const event = JSON.parse(jsonStr);

              // Handle different event types
              if (event.type === 'agent_start') {
                addLog('STATUS', `🤖 ${event.agent} started working...`);
              } else if (event.type === 'token') {
                // Stream tokens from different agents
                if (event.agent === 'carlos') {
                  carlosDesign += event.content;
                  setDesignDoc(carlosDesign);
                } else if (event.agent === 'ronei_design') {
                  roneiDesign += event.content;
                } else if (event.agent === 'requirements_gathering') {
                  // Stream requirements questions in real-time
                  setStreamingQuestions(prev => prev + event.content);
                }
              } else if (event.type === 'field_update') {
                addLog('DATA', `📊 ${event.field} updated`);
              } else if (event.type === 'agent_complete') {
                addLog('SUCCESS', `✅ ${event.agent} completed`);
              } else if (event.type === 'complete') {
                // Final event with complete state
                const summary = event.summary;

                // Check if clarification is needed
                if (summary.clarification_needed) {
                  setClarificationNeeded(true);
                  // Extract just the questions from agent_chat (remove "**Requirements Team:**\n" prefix)
                  const questionsText = summary.agent_chat.replace(/^\*\*Requirements Team:\*\*\n?/, '').trim();
                  setClarificationQuestions(questionsText);
                  setStreamingQuestions(""); // Clear streaming state
                  setDesignDoc(""); // Clear design doc
                  setStatus("awaiting_answers");
                  addLog('INFO', '❓ Carlos and Ronei need more information');
                } else {
                  // Show full design with all sections
                  let fullDoc = "# Carlos's Design\n\n" + summary.design + "\n\n";
                  fullDoc += "---\n\n# Ronei's Design\n\n" + summary.ronei_design + "\n\n";
                  fullDoc += "---\n\n# Security Report\n\n" + summary.security_report + "\n\n";
                  fullDoc += "---\n\n# Cost Analysis\n\n" + summary.cost_report + "\n\n";
                  fullDoc += "---\n\n# Reliability Report\n\n" + summary.reliability_report + "\n\n";
                  fullDoc += "---\n\n# Audit Report\n\n" + summary.audit_report + "\n\n";
                  fullDoc += "---\n\n# Recommendation\n\n" + summary.recommendation + "\n\n";
                  if (summary.terraform_code) {
                    fullDoc += "---\n\n# Terraform Code\n\n" + summary.terraform_code;
                  }
                  setDesignDoc(fullDoc);
                  setStreamingQuestions(""); // Clear streaming state
                  setClarificationNeeded(false);
                  setStatus("idle");
                }
              } else if (event.type === 'error') {
                throw new Error(event.message);
              }

            } catch (e) {
              addLog('ERROR', 'Failed to parse stream event', e.message);
            }
          }
        }
      }

      if (status === "designing") {
        setStatus("idle");
      }

    } catch (error) {
      addLog('ERROR', '❌ Architect failed to respond', { message: error.message });
      setStatus("error");
    }
  };

  const submitAnswers = async () => {
    if (!userAnswers.trim()) return;

    setClarificationNeeded(false);
    setInput(originalRequirements); // Restore original requirements for the second call
    await runCarlos(userAnswers);
    setUserAnswers(""); // Clear answers after submission
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file size (50MB - increased for async processing)
    const maxSize = 50 * 1024 * 1024;
    if (file.size > maxSize) {
      addLog('ERROR', '❌ File too large. Maximum size is 50MB');
      return;
    }

    setUploading(true);
    addLog('INFO', `📤 Uploading ${file.name}...`);

    try {
      const formData = new FormData();
      formData.append('file', file);

      // Start async document processing
      const response = await fetch(`${backendBaseUrl}/upload-document`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formData
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Upload failed');
      }

      const data = await response.json();
      const taskId = data.task_id;

      addLog('INFO', `⏳ Processing ${file.name}...`);

      // Poll for completion
      const pollInterval = 2000; // 2 seconds
      const maxAttempts = 60; // 2 minutes max
      let attempts = 0;

      const checkStatus = async () => {
        try {
          const statusResponse = await fetch(`${backendBaseUrl}/documents/${taskId}`, {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`
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
              addLog('ERROR', `❌ Document ${file.name} completed but no text was extracted`);
              setUploading(false);
              return;
            }

            // Merge extracted text with existing input
            const mergedText = input.trim()
              ? `${input.trim()}\n\n${extractedText}`
              : extractedText;

            setInput(mergedText);
            setUploadedFile({ name: file.name, message: `✅ ${file.name} processed successfully` });

            addLog('SUCCESS', `✅ ${file.name} processed successfully`);
            setUploading(false);

            // Clear the file after a few seconds
            setTimeout(() => setUploadedFile(null), 5000);

          } else if (statusData.status === 'failed') {
            addLog('ERROR', `❌ Failed to process ${file.name}: ${statusData.error || 'Unknown error'}`);
            setUploading(false);

          } else {
            // Still processing, check again
            attempts++;
            if (attempts < maxAttempts) {
              setTimeout(checkStatus, pollInterval);
            } else {
              addLog('ERROR', `❌ Document processing timeout after ${maxAttempts * pollInterval / 1000}s`);
              setUploading(false);
            }
          }

        } catch (error) {
          addLog('ERROR', `❌ Status check failed: ${error.message}`);
          setUploading(false);
        }
      };

      // Start polling
      checkStatus();

    } catch (error) {
      addLog('ERROR', `❌ Upload failed: ${error.message}`);
      setUploading(false);
    } finally {
      // Reset file input
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

  if (loading) return <SplashScreen />;

  return (
    <div className="flex h-screen bg-slate-50 font-sans text-slate-900">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 text-slate-300 border-r p-6 flex flex-col gap-4">
        
        {/* Carlos Sidebar Avatar */}
        <div className="flex items-center gap-3 mb-8 group cursor-pointer">
          <div className="relative">
            <img 
              src={carlosImg}
              alt="Carlos AI" 
              className="w-12 h-12 rounded-full object-cover border-2 border-blue-500 shadow-lg group-hover:scale-110 transition-transform duration-200"
            />
            <span className={`absolute bottom-0 right-0 block h-3 w-3 rounded-full ring-2 ring-slate-900 ${
              status === 'designing' ? 'bg-blue-400 animate-ping' :
              status === 'awaiting_answers' ? 'bg-amber-400 animate-pulse' :
              'bg-green-500'
            }`} />
          </div>
          <div className="flex flex-col">
            <h1 className="font-bold text-white text-lg leading-tight">Carlos AI</h1>
            <span className="text-[10px] uppercase tracking-widest text-slate-500 font-bold">Chief Architect</span>
          </div>
        </div>

        <nav className="flex flex-col gap-2">
          <button className="flex items-center gap-2 p-2 bg-blue-600 text-white rounded-md font-medium"><PenTool size={18}/> New Design</button>
          <button className="flex items-center gap-2 p-2 hover:bg-slate-800 rounded-md transition-colors"><Cloud size={18}/> My Infrastructure</button>
          <button className="flex items-center gap-2 p-2 hover:bg-slate-800 rounded-md transition-colors"><ShieldCheck size={18}/> Security Audits</button>
        </nav>
        
        <div className="mt-auto pt-4 border-t border-slate-800">
          <button 
            onClick={() => setShowDebug(!showDebug)}
            className="flex items-center gap-2 p-2 text-slate-500 hover:bg-slate-800 rounded-md w-full transition-colors"
          >
            <Terminal size={18}/> {showDebug ? 'Hide' : 'Show'} Debug
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col">
        <header className="p-4 border-b bg-white flex justify-between items-center px-8 shadow-sm">
          <span className="text-xs uppercase tracking-widest font-bold text-slate-400">Azure Design Studio</span>
          <div className="flex items-center gap-4">
            {status === 'designing' && (
               <div className="flex items-center gap-2 text-blue-600">
                 <Loader2 className="animate-spin" size={16}/>
                 <span className="text-sm font-bold tracking-tight uppercase">Carlos is {status}...</span>
               </div>
            )}
            {status === 'awaiting_answers' && (
               <div className="flex items-center gap-2 text-amber-600">
                 <span className="text-sm font-bold tracking-tight uppercase">⏳ Awaiting your answers</span>
               </div>
            )}
            {status === 'error' && <span className="text-sm font-bold text-red-500">SYSTEM ERROR</span>}
          </div>
        </header>
        
        <div className="flex-1 overflow-auto p-8 flex gap-6">
          {/* Markdown Output Area */}
          <div className={`${showDebug ? 'w-2/3' : 'w-full'} transition-all duration-300`}>
            <div className="max-w-4xl mx-auto bg-white p-12 rounded-2xl shadow-xl border border-slate-200 min-h-full prose prose-slate lg:prose-xl">
              {clarificationNeeded ? (
                <ClarificationForm
                  questions={clarificationQuestions}
                  userAnswers={userAnswers}
                  setUserAnswers={setUserAnswers}
                  onSubmit={submitAnswers}
                  loading={status === 'designing'}
                />
              ) : streamingQuestions && status === 'designing' ? (
                // Show streaming questions while Requirements Team is working
                <StreamingQuestionsView questions={streamingQuestions} />
              ) : designDoc ? (
                <ReactMarkdown>{designDoc}</ReactMarkdown>
              ) : (
                <EmptyState />
              )}
            </div>
          </div>

          {/* Debug Console Panel */}
          {showDebug && (
            <div className="w-1/3 bg-slate-950 text-slate-300 rounded-2xl p-5 overflow-auto font-mono text-[11px] shadow-2xl border border-slate-800">
              <div className="flex justify-between items-center mb-4 sticky top-0 bg-slate-950 pb-2 border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-red-500" />
                  <div className="w-2 h-2 rounded-full bg-yellow-500" />
                  <div className="w-2 h-2 rounded-full bg-green-500" />
                  <h3 className="ml-2 font-bold text-slate-500">DEBUG_LOG</h3>
                </div>
                <button onClick={() => setDebugLog([])} className="hover:text-white underline">clear</button>
              </div>
              
              {debugLog.length === 0 ? (
                <div className="text-slate-700 italic text-center py-20">Awaiting architectural input...</div>
              ) : (
                <div className="space-y-3">
                  {debugLog.map((log, i) => (
                    <div key={i} className={`border-l-2 pl-3 py-1 ${getLogColor(log.type)}`}>
                      <div className="flex gap-2 text-slate-500 opacity-70">
                        <span>{log.timestamp}</span>
                        <span className="font-bold">[{log.type}]</span>
                      </div>
                      <div className="mt-1 text-slate-200">{log.message}</div>
                      {log.data && (
                        <pre className="mt-2 bg-black/40 p-2 rounded text-[10px] text-blue-300 overflow-x-auto border border-white/5">
                          {typeof log.data === 'string' ? log.data : JSON.stringify(log.data, null, 2)}
                        </pre>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Requirements Input Area */}
        {!clarificationNeeded && (
          <footer className="p-8 bg-white border-t border-slate-200 shadow-[0_-4px_20px_-5px_rgba(0,0,0,0.05)]">
            <div className="max-w-4xl mx-auto">
              {/* File upload confirmation */}
              {uploadedFile && (
                <div className="mb-3 p-3 bg-blue-50 border border-blue-200 rounded-lg flex items-center justify-between">
                  <div className="flex items-center gap-2 text-blue-700">
                    <Paperclip size={16} />
                    <span className="text-sm font-medium">{uploadedFile.message}</span>
                  </div>
                  <button
                    onClick={removeUploadedFile}
                    className="text-blue-500 hover:text-blue-700 transition-colors"
                  >
                    <X size={16} />
                  </button>
                </div>
              )}

              <div className="flex gap-4">
                {/* Hidden file input */}
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.docx,.doc,.txt,.md,.xlsx,.xls"
                  onChange={handleFileUpload}
                  className="hidden"
                />

                {/* Paperclip button */}
                <button
                  onClick={handleFileButtonClick}
                  disabled={status === 'designing' || uploading}
                  className="bg-slate-100 hover:bg-slate-200 text-slate-700 p-4 rounded-xl transition-all disabled:opacity-30 disabled:cursor-not-allowed border border-slate-200"
                  title="Upload requirements document (PDF, DOCX, TXT, MD, XLSX - max 10MB)"
                >
                  {uploading ? (
                    <Loader2 className="animate-spin" size={20} />
                  ) : (
                    <Paperclip size={20} />
                  )}
                </button>

                <input
                  className="flex-1 p-4 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none transition-all placeholder:text-slate-400"
                  placeholder="Tell Carlos your cloud requirements (e.g. 'Highly available AKS cluster on Azure')..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && !clarificationNeeded && runCarlos()}
                  disabled={status === 'designing'}
                />
                <button
                  onClick={() => runCarlos()}
                  disabled={!input.trim() || status === 'designing'}
                  className="bg-blue-600 text-white px-10 py-4 rounded-xl font-bold hover:bg-blue-700 active:scale-95 transition-all disabled:opacity-30 shadow-lg shadow-blue-500/20"
                >
                  {status === 'designing' ? 'Designing...' : 'Ask Carlos'}
                </button>
              </div>
            </div>
          </footer>
        )}
      </main>
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
        <ReactMarkdown className="prose prose-slate max-w-none">{questions}</ReactMarkdown>
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

// Helper: Color logic for debug log borders
function getLogColor(type) {
  switch(type) {
    case 'ERROR': return 'border-red-500';
    case 'SUCCESS': return 'border-green-500';
    case 'WARN': return 'border-yellow-500';
    case 'DATA': return 'border-blue-500/30';
    case 'PARSE': return 'border-purple-500';
    case 'STATUS': return 'border-cyan-500';
    default: return 'border-slate-800';
  }
}

function EmptyState() {
  return (
    <div className="text-center py-32 opacity-20 italic">
      <Cloud size={80} className="mx-auto mb-6 text-slate-400" />
      <p className="text-2xl font-light">Architectural blueprints will stream here...</p>
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
        <ReactMarkdown className="prose prose-slate max-w-none">{questions}</ReactMarkdown>
        <span className="inline-block w-2 h-5 bg-blue-500 animate-pulse ml-1" />
      </div>
    </div>
  );
}

function SplashScreen() {
  return (
    <div className="h-screen w-screen flex flex-col items-center justify-center bg-slate-900 text-white">
      <div className="relative mb-12 animate-in zoom-in duration-1000">
        <img 
          src={carlosImg}
          alt="Carlos Drafting" 
          className="w-72 h-72 rounded-full border-[12px] border-white/10 shadow-[0_0_50px_rgba(37,99,235,0.4)] object-cover" 
        />
        <div className="absolute -bottom-6 left-1/2 -translate-x-1/2 bg-blue-600 px-6 py-2 rounded-full font-black tracking-widest shadow-xl">
          CHIEF ARCHITECT
        </div>
      </div>
      <h1 className="text-5xl font-black tracking-tighter uppercase mb-4">Carlos AI</h1>
      <p className="text-blue-400 font-bold animate-pulse tracking-widest text-sm uppercase">Sharpening Digital Pencils</p>
    </div>
  );
}