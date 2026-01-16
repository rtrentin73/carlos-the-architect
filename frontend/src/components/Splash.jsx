import React from 'react';
import splashImg from '../assets/splash.jpg';

export default function Splash() {
  return (
    <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-white animate-in fade-in duration-1000">
      <div className="relative">
        {/* Place the splash.png image you generated in your public folder */}
        <img 
          src={splashImg} 
          alt="Carlos Drafting" 
          className="w-64 h-64 rounded-full border-4 border-blue-600 shadow-2xl animate-pulse" 
        />
        <div className="absolute -bottom-4 left-1/2 -translate-x-1/2 bg-blue-600 text-white px-4 py-1 rounded-full text-sm font-bold">
          CARLOS IS READY
        </div>
      </div>
      <h1 className="mt-8 text-3xl font-black text-slate-800 tracking-tighter uppercase">
        Carlos the Architect
      </h1>
      <p className="text-slate-400 font-medium italic mt-2">Designing your future, one bone at a time...</p>
    </div>
  );
}
