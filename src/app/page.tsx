"use client";

import { useState, useRef } from "react";
// import json from "json";

const DEFAULT_CODE = `from manim import *

class HelloWorld(Scene):
    def construct(self):
        text = Text("Hello, Manim!")
        self.play(Write(text))
        self.wait(1)
`;

export default function Home() {
  const [code, setCode] = useState(DEFAULT_CODE);
  const [scene, setScene] = useState("HelloWorld");
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const [analyzing, setAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState<any>(null);
  const [input, setInput] = useState("");

  // const [analyzingG, setAnalyzingG] = useState(false);
  // const [analysisG, setAnalysisG] = useState<any>(null);

  const [videoPath, setVideoPath] = useState<string | null>(null);

  const videoRef = useRef<HTMLVideoElement>(null);

  async function handleRender() {
    setLoading(true);
    setError(null);
    setVideoUrl(null);

    try {
      const res = await fetch("/api/render", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code, scene }),
      });

      if (!res.ok) {
        const err = await res.json();
        setError(err.error || "Render failed");
        return;
      }

      const data = await res.json();
      setVideoUrl(data.videoUrl);   // used by <video src="">
      setVideoPath(data.videoPath); // used by analyze

      setTimeout(() => videoRef.current?.play(), 100);
    } catch (e) {
      setError("Network error — is the container running?");
    } finally {
      setLoading(false);
    }
  }

  async function handleAnalyze() {
    if (!videoPath) return;

    setAnalyzing(true);
    setAnalysis(null);
    setError(null); 

    try {
      const res = await fetch("http://localhost:8000/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ video_path: videoPath, code: code }),
      });

      if (!res.ok) {
        const err = await res.json();
        setError(err.detail || "Analysis failed");
        return;
      }

      const data = await res.json();
      setAnalysis(data);
    } catch (e) {
      setError("Analysis request failed — is FastAPI running?");
    } finally {
      setAnalyzing(false);
    }
  }


  async function handleSend() {
    if (!input) return;
    try {
      const res = await fetch("http://localhost:8000/gemini_code", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ algorithm: input }),
      });

      // if (!res.ok) {
      //   const err = await res.json();
      //   setError(err.detail || "prompt input failed");
      //   return;
      // }

      // const data = await res.json();
      // setCode(data.text);
    } catch (e) {
      setError("i can't get the user's prompt grrrrr");
    }
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-8">


      <div className="rounded-xl border border-zinc-700 bg-zinc-900/60 p-3">
        <label className="mb-2 block text-sm text-zinc-300">Prompt</label>
        <div className="flex items-center gap-2">
          <input
            type="text"
            className="w-full rounded-full border border-zinc-600 bg-zinc-950 px-4 py-2 text-sm text-zinc-100 placeholder:text-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-400"
            placeholder="Type a message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />
          <button
            onClick={handleSend}
            type="button"
            className="rounded-full bg-zinc-100 px-4 py-2 text-sm font-medium text-zinc-900 transition hover:bg-zinc-300"
          >
            Send
          </button>
        </div>
      </div>

      <div className="space-y-2">
        <label className="text-sm">Scene class name</label>
        <input
          className="w-full rounded border border-black px-3 py-2 font-mono text-sm focus:outline-none focus:ring-1 focus:ring-black"
          value={scene}
          onChange={(e) => setScene(e.target.value)}
        />
      </div>

      <div className="space-y-2">
        <label className="text-gray text-sm">Manim code</label>
        <textarea
          className="h-72 w-full resize-y rounded border bg-black px-3 py-2 font-mono text-sm focus:outline-none focus:ring-1 focus:ring-black"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          spellCheck={false}
        />
      </div>

      <button
        onClick={handleRender}
        disabled={loading}
        className="rounded bg-white px-6 py-2 font-semibold text-black transition hover:bg-gray-200 disabled:opacity-40"
      >
        {loading ? "Rendering…" : "Render"}
      </button>

      {error && (
        <pre className="overflow-auto rounded border border-red-700 bg-red-950 p-4 text-xs text-red-300">
          {error}
        </pre>
      )}

      {videoUrl && (
        <div className="space-y-2">
          <p className="text-sm text-gray-400">Output</p>
          <video
            ref={videoRef}
            src={videoUrl}
            controls
            className="w-full max-h-[50vh] object-contain rounded border bg-black"
          />

          <button
            onClick={handleAnalyze}
            disabled={analyzing}
            className="rounded bg-blue-600 px-6 py-2 font-semibold text-white hover:bg-blue-700 disabled:opacity-40"
          >
            {analyzing ? "Analyzing…" : "Analyze"}
          </button>
        </div>
      )}
    </div>
  );
}
