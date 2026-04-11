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

  const [analyzingTL, setAnalyzingTL] = useState(false);
  const [analysisTL, setAnalysisTL] = useState<any>(null);

  const [analyzingG, setAnalyzingG] = useState(false);
  const [analysisG, setAnalysisG] = useState<any>(null);

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

      // const blob = await res.blob();
      // const url = URL.createObjectURL(blob);
      // setVideoUrl(url);
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

  async function handleAnalyzeTL() {
    if (!videoPath) return;

    setAnalyzingTL(true);
    setAnalysisTL(null);
    setError(null); 

    try {
      const res = await fetch("http://localhost:8000/tl_analysis", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        // NOTE: replace videoUrl with a publicly accessible URL in production
        // Local blob URLs won't work with TwelveLabs — they can't reach your machine
        // body: JSON.stringify({ video_url: videoUrl }),
        body: JSON.stringify({ video_path: videoPath }),
      });

      if (!res.ok) {
        const err = await res.json();
        setError(err.detail || "Analysis failed");
        return;
      }

      const data = await res.json();
      setAnalysisTL(data);
    } catch (e) {
      setError("Analysis request failed — is FastAPI running?");
    } finally {
      setAnalyzingTL(false);
    }
  }

  async function handleAnalyzeG() {
    if (!videoPath) return;

    setAnalyzingG(true);
    setAnalysisG(null);
    setError(null); 

    try {
      const res = await fetch("http://localhost:8000/gemini_analysis", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        // NOTE: replace videoUrl with a publicly accessible URL in production
        // Local blob URLs won't work with TwelveLabs — they can't reach your machine
        // body: JSON.stringify({ video_url: videoUrl }),
        body: JSON.stringify({ video_path: videoPath }),
      });

      if (!res.ok) {
        const err = await res.json();
        setError(err.detail || "Analysis failed");
        return;
      }

      const data = await res.json();
      setAnalysisG(data);
    } catch (e) {
      setError("Analysis request failed — is FastAPI running?");
    } finally {
      setAnalyzingG(false);
    }
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-8">
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
          onClick={handleAnalyzeTL}
          disabled={analyzingTL}
          className="rounded bg-blue-600 px-6 py-2 font-semibold text-white hover:bg-blue-700 disabled:opacity-40"
        >
          {analyzingTL ? "Analyzing…" : "Analyze with TwelveLabs"}
        </button>
        <button
          onClick={handleAnalyzeG}
          disabled={analyzingG}
          className="rounded bg-blue-600 px-6 py-2 font-semibold text-white hover:bg-blue-700 disabled:opacity-40"
        >
          {analyzingG ? "Analyzing…" : "Analyze with Gemini"}
        </button>
          </div>
      )}

      {/* Analysis results */}
      {analysisTL && (
        <div className="space-y-3 rounded border border-gray-700 p-4">
          <div className="flex items-center gap-3">
            <span
              className={`rounded px-2 py-1 text-xs font-bold bg-green-900 text-green-300 ${
                JSON.parse(analysisTL.data).passed
                  ? "bg-green-900 text-green-300"
                  : "bg-red-900 text-red-300"
              }`}
            >
              {JSON.parse(analysisTL.data).passed ? "PASSED" : "FAILED"}
            </span>
            <pre className="text-sm text-gray-300">{JSON.stringify({ ...analysisTL, data: JSON.parse(analysisTL.data) }, null, 2)}</pre>
            {/* <p className="text-white text-xs">{typeof JSON.parse(analysis.data).passed} — {JSON.parse(analysis.data).passed.toString()}</p> */}
            <p className="text-sm text-black">{JSON.parse(analysisTL.data).passed.toString()}</p>
          </div>

          {analysisTL.errors?.length > 0 && (
            <div className="space-y-2">
              <p className="text-sm font-semibold text-red-400">Errors</p>
              {analysisTL.errors.map((err: any, i: number) => (
                <div key={i} className="rounded border border-gray-700 p-3 text-xs space-y-1">
                  <div className="flex gap-2">
                    <span className={`font-bold uppercase ${
                      err.severity === "critical" ? "text-red-400" :
                      err.severity === "major" ? "text-orange-400" : "text-yellow-400"
                    }`}>
                      {err.severity}
                    </span>
                    <span className="text-gray-400">{err.category}</span>
                    <span className="text-gray-500">{err.timestamp}</span>
                  </div>
                  <p className="text-gray-300">{err.description}</p>
                  <p className="text-blue-400">Fix: {err.suggested_fix}</p>
                </div>
              ))}
            </div>
          )}

          <p className="text-xs text-gray-500">
            Recommendation: <span className="font-bold text-white">{analysisTL.iteration_recommendation}</span>
          </p>
          {analysisG && (
            <div className="space-y-3 rounded border border-gray-700 p-4">
              <pre className="text-sm text-gray-300">{JSON.stringify({ ...analysisG, data: JSON.parse(analysisG.data) }, null, 2)}</pre>
              <p className="text-sm text-black">{JSON.parse(analysisG.data).passed.toString()}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
