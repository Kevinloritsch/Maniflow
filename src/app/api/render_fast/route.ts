import { NextRequest, NextResponse } from "next/server";
import fs from "fs";
import path from "path";

export async function POST(req: NextRequest) {
  const body = await req.json();

  const res = await fetch(`${process.env.MANIM_API_URL}/render_fast`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const text = await res.text();
    let errMsg = text;
    try {
      errMsg = JSON.parse(text).error;
    } catch {}
    return NextResponse.json({ error: errMsg }, { status: res.status });
  }

  const renderDurationMs = Number(res.headers.get("x-render-duration-ms") ?? 0);
  const videoBuffer = await res.arrayBuffer();

  const filename = `output_${Date.now()}_${Math.random().toString(36).slice(2)}.mp4`;
  const rendersDir = path.join(process.cwd(), "public", "renders");
  const filepath = path.join(rendersDir, filename);

  try {
    fs.mkdirSync(rendersDir, { recursive: true });
    fs.writeFileSync(filepath, Buffer.from(videoBuffer));
  } catch (err) {
    console.error("Failed to save video:", err);
    return NextResponse.json(
      { error: "Failed to save rendered video" },
      { status: 500 },
    );
  }

  return NextResponse.json({
    videoUrl: `/renders/${filename}`,
    videoPath: filepath,
    renderDurationMs,
  });
}
