import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Cloud, ShieldCheck, PenTool, Loader2, Terminal } from 'lucide-react';
import carlosImg from './assets/splash.jpg';

export default function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [input, setInput] = useState("");
  const [designDoc, setDesignDoc] = useState("");
  const [status, setStatus] = useState("idle"); // idle, designing, auditing, error
  const [debugLog, setDebugLog] = useState([]);
  const [showDebug, setShowDebug] = useState(true);

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

  const runCarlos = async () => {
    if (!input.trim()) return;
    
    setDesignDoc("");
    setDebugLog([]); 
    setStatus("designing");
    
    addLog('INFO', '📤 Sending request to Carlos...', { requirements: input });

    try {
      const response = await fetch("http://localhost:8000/design", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ requirements: input }),
      });

      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let chunkCount = 0;

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
        
        lines.forEach((line) => {
          if (line.startsWith("data: ")) {
            try {
              const jsonStr = line.replace("data: ", "");
              if (jsonStr === "DONE") return;
              
              const data = JSON.parse(jsonStr);
              if (data.token) setDesignDoc((prev) => prev + data.token);
              if (data.status) setStatus(data.status);
              
            } catch (e) {
              addLog('ERROR', 'Failed to parse stream line', e.message);
            }
          }
        });
      }
      setStatus("idle");
      
    } catch (error) {
      addLog('ERROR', '❌ Architect failed to respond', { message: error.message });
      setStatus("error");
    }
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
            <span className={`absolute bottom-0 right-0 block h-3 w-3 rounded-full ring-2 ring-slate-900 ${status === 'designing' ? 'bg-blue-400 animate-ping' : 'bg-green-500'}`} />
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
            {status !== 'idle' && status !== 'error' && (
               <div className="flex items-center gap-2 text-blue-600">
                 <Loader2 className="animate-spin" size={16}/>
                 <span className="text-sm font-bold tracking-tight uppercase">Carlos is {status}...</span>
               </div>
            )}
            {status === 'error' && <span className="text-sm font-bold text-red-500">SYSTEM ERROR</span>}
          </div>
        </header>
        
        <div className="flex-1 overflow-auto p-8 flex gap-6">
          {/* Markdown Output Area */}
          <div className={`${showDebug ? 'w-2/3' : 'w-full'} transition-all duration-300`}>
            <div className="max-w-4xl mx-auto bg-white p-12 rounded-2xl shadow-xl border border-slate-200 min-h-full prose prose-slate lg:prose-xl">
              {designDoc ? <ReactMarkdown>{designDoc}</ReactMarkdown> : <EmptyState />}
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
        <footer className="p-8 bg-white border-t border-slate-200 shadow-[0_-4px_20px_-5px_rgba(0,0,0,0.05)]">
          <div className="max-w-4xl mx-auto flex gap-4">
            <input 
              className="flex-1 p-4 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none transition-all placeholder:text-slate-400"
              placeholder="Tell Carlos your cloud requirements (e.g. 'Highly available AKS cluster on Azure')..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && runCarlos()}
            />
            <button 
              onClick={runCarlos}
              disabled={!input.trim() || status === 'designing'}
              className="bg-blue-600 text-white px-10 py-4 rounded-xl font-bold hover:bg-blue-700 active:scale-95 transition-all disabled:opacity-30 shadow-lg shadow-blue-500/20"
            >
              Ask Carlos
            </button>
          </div>
        </footer>
      </main>
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