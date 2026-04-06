"use client";

import { useState, useRef } from "react";

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

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      setVideoUrl(url);
      setTimeout(() => videoRef.current?.play(), 100);
    } catch (e) {
      setError("Network error — is the container running?");
    } finally {
      setLoading(false);
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
            className="w-full rounded border bg-black"
          />
        </div>
      )}
    </div>
  );
}
