import React from 'react';
export default function App() {
  return (
    <div className="bg-black text-cyan-400 min-h-screen p-10 font-mono">
      <h1 className="text-2xl border-b border-cyan-900 pb-2 animate-pulse">ICE GODS COMMAND</h1>
      <div className="mt-8 grid grid-cols-2 gap-4">
        <div className="border border-cyan-900 p-4">SUPPLY: 30B</div>
        <div className="border border-cyan-900 p-4">FEE: 1%</div>
      </div>
    </div>
  );
}
