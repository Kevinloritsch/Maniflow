import { NextRequest, NextResponse } from "next/server";

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

  const videoBuffer = await res.arrayBuffer();
  return new NextResponse(videoBuffer, {
    headers: { "Content-Type": "video/mp4" },
  });
}
