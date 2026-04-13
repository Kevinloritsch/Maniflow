import { NextRequest, NextResponse } from "next/server";
import fs from "fs";
import path from "path";

export async function POST(req: NextRequest) {
  const body = await req.json();

  const res = await fetch(`${process.env.MANIM_API_URL}/render`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const err = await res.json();
    return NextResponse.json(err, { status: res.status });
  }

  const renderDurationMs = Number(res.headers.get("x-render-duration-ms") ?? 0);
  const videoBuffer = await res.arrayBuffer();

  const filename = `output_${Date.now()}_${Math.random().toString(36).slice(2)}.mp4`;
  const rendersDir = path.join(process.cwd(), "public", "renders");
  const filepath = path.join(rendersDir, filename);

  fs.mkdirSync(rendersDir, { recursive: true });
  fs.writeFileSync(filepath, Buffer.from(videoBuffer));

  return NextResponse.json({
    videoUrl: `/renders/${filename}`,
    videoPath: filepath,
    renderDurationMs,
  });
}
