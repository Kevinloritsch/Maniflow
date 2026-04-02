// import { NextRequest, NextResponse } from "next/server";

// export async function POST(req: NextRequest) {
//   const body = await req.json();

//   const res = await fetch(`${process.env.MANIM_API_URL}/render`, {
//     method: "POST",
//     headers: { "Content-Type": "application/json" },
//     body: JSON.stringify(body),
//   });

//   if (!res.ok) {
//     const err = await res.json();
//     return NextResponse.json(err, { status: res.status });
//   }

//   const videoBuffer = await res.arrayBuffer();
//   return new NextResponse(videoBuffer, {
//     headers: { "Content-Type": "video/mp4" },
//   });
// }

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

  const videoBuffer = await res.arrayBuffer();

  try {
    const filename = `output_${Date.now()}.mp4`;
    const rendersDir = path.join(process.cwd(), "public", "renders");
    const filepath = path.join(rendersDir, filename);

    fs.mkdirSync(rendersDir, { recursive: true });
    fs.writeFileSync(filepath, Buffer.from(videoBuffer));

    return NextResponse.json({
      videoUrl: `/renders/${filename}`,  // relative URL for <video src="">
      videoPath: filepath,               // absolute path for FastAPI
    });
  } catch (err) {
    console.error("File save error:", err);
    return NextResponse.json(
      { error: `Failed to save video: ${err}` },
      { status: 500 }
    );
  }
}