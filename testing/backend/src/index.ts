import express from "express";
import cors from "cors";
import multer from "multer";
import path from "path";
import fs from "fs";
import axios from "axios";
import FormData from "form-data";
import { z } from "zod";
import { PrismaClient } from "@prisma/client";
import net from "net";

const prisma = new PrismaClient();

const app = express();
const desiredPort = Number(process.env.PORT || 5000);
const pramanaBaseUrl = process.env.PRAMANA_BASE_URL || "http://74.225.160.195:8080";
const uploadDir = path.join(process.cwd(), "uploads");

if (!fs.existsSync(uploadDir)) {
  fs.mkdirSync(uploadDir, { recursive: true });
}

app.use(cors({ origin: "http://localhost:5173" }));
app.use(express.json());
app.use("/uploads", express.static(uploadDir));

const storage = multer.diskStorage({
  destination: (_req, _file, cb) => cb(null, uploadDir),
  filename: (_req, file, cb) => {
    const ext = path.extname(file.originalname) || ".bin";
    const unique = `${Date.now()}-${Math.round(Math.random() * 1e9)}`;
    cb(null, `${unique}${ext}`);
  },
});

const upload = multer({ storage });

const postSchema = z.object({
  title: z.string().min(1),
  description: z.string().min(1),
});

const postUpdateSchema = z.object({
  title: z.string().min(1).optional(),
  description: z.string().min(1).optional(),
});

type VerificationPayload = {
  verdict?: string;
  truth_score?: number;
  truthScore?: number;
  confidence?: string;
  explanation?: string;
  citations?: unknown;
  cached?: boolean;
};

type VerificationResult = {
  verificationJson: string;
  verdict: string | null;
  truthScore: number | null;
  confidence: string | null;
  explanation: string | null;
};

function combinedText(title: string, description: string) {
  return `${title}\n\n${description}`.trim();
}

function imageFilePath(imagePath: string) {
  return path.join(uploadDir, path.basename(imagePath));
}

async function verifyWithPramana(title: string, description: string, imagePath?: string | null): Promise<VerificationResult> {
  const text = combinedText(title, description);
  try {
    let responseData: any;
    if (imagePath) {
      const form = new FormData();
      form.append("text", text);
      form.append("mode", "fast");
      form.append("language", "en");
      form.append("file", fs.createReadStream(imageFilePath(imagePath)));
      const resp = await axios.post(`${pramanaBaseUrl}/v1/verify`, form, {
        headers: form.getHeaders(),
        maxBodyLength: Infinity,
        timeout: 30000,
      });
      responseData = resp.data;
    } else {
      const resp = await axios.post(
        `${pramanaBaseUrl}/verify`,
        { content_type: "text", text, client_id: "testing-web" },
        { timeout: 30000 }
      );
      responseData = resp.data;
    }

    const payload = responseData as VerificationPayload;
    const truthScore = typeof payload.truth_score === "number" ? payload.truth_score : payload.truthScore;
    return {
      verificationJson: JSON.stringify(responseData),
      verdict: payload.verdict ?? null,
      truthScore: typeof truthScore === "number" ? truthScore : null,
      confidence: payload.confidence ?? null,
      explanation: payload.explanation ?? null,
    };
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    const fallback = {
      verdict: "unknown",
      truth_score: 0.5,
      confidence: "low",
      explanation: `Pramana verification failed: ${message}`,
      citations: [],
      cached: false,
    };
    return {
      verificationJson: JSON.stringify(fallback),
      verdict: "unknown",
      truthScore: 0.5,
      confidence: "low",
      explanation: fallback.explanation,
    };
  }
}

function toApiPost(post: any) {
  const verification = post.verificationJson ? JSON.parse(post.verificationJson) : null;
  return { ...post, verification };
}

app.get("/api/health", (_req, res) => {
  res.json({ ok: true });
});

app.get("/api/posts", async (_req, res) => {
  const posts = await prisma.post.findMany({ orderBy: { createdAt: "desc" } });
  res.json(posts.map(toApiPost));
});

app.get("/api/posts/:id", async (req, res) => {
  const post = await prisma.post.findUnique({ where: { id: req.params.id } });
  if (!post) {
    res.status(404).json({ error: "Post not found" });
    return;
  }
  res.json(toApiPost(post));
});

app.post("/api/posts", upload.single("image"), async (req, res) => {
  const parsed = postSchema.safeParse(req.body);
  if (!parsed.success) {
    res.status(400).json({ error: parsed.error.flatten() });
    return;
  }

  const { title, description } = parsed.data;
  const imagePath = req.file ? `/uploads/${req.file.filename}` : null;

  const verification = await verifyWithPramana(title, description, imagePath);

  const created = await prisma.post.create({
    data: {
      title,
      description,
      imagePath,
      verificationJson: verification.verificationJson,
      verdict: verification.verdict,
      truthScore: verification.truthScore,
      confidence: verification.confidence,
      explanation: verification.explanation,
    },
  });

  res.status(201).json(toApiPost(created));
});

app.put("/api/posts/:id", upload.single("image"), async (req, res) => {
  const post = await prisma.post.findUnique({ where: { id: req.params.id } });
  if (!post) {
    res.status(404).json({ error: "Post not found" });
    return;
  }

  const parsed = postUpdateSchema.safeParse(req.body);
  if (!parsed.success) {
    res.status(400).json({ error: parsed.error.flatten() });
    return;
  }

  const title = parsed.data.title ?? post.title;
  const description = parsed.data.description ?? post.description;
  const imagePath = req.file ? `/uploads/${req.file.filename}` : post.imagePath;

  const verification = await verifyWithPramana(title, description, imagePath);

  const updated = await prisma.post.update({
    where: { id: post.id },
    data: {
      title,
      description,
      imagePath,
      verificationJson: verification.verificationJson,
      verdict: verification.verdict,
      truthScore: verification.truthScore,
      confidence: verification.confidence,
      explanation: verification.explanation,
    },
  });

  res.json(toApiPost(updated));
});

app.delete("/api/posts/:id", async (req, res) => {
  const post = await prisma.post.findUnique({ where: { id: req.params.id } });
  if (!post) {
    res.status(404).json({ error: "Post not found" });
    return;
  }
  await prisma.post.delete({ where: { id: post.id } });
  res.status(204).send();
});

app.post("/api/posts/:id/verify", async (req, res) => {
  const post = await prisma.post.findUnique({ where: { id: req.params.id } });
  if (!post) {
    res.status(404).json({ error: "Post not found" });
    return;
  }

  const verification = await verifyWithPramana(post.title, post.description, post.imagePath);

  const updated = await prisma.post.update({
    where: { id: post.id },
    data: {
      verificationJson: verification.verificationJson,
      verdict: verification.verdict,
      truthScore: verification.truthScore,
      confidence: verification.confidence,
      explanation: verification.explanation,
    },
  });

  res.json(toApiPost(updated));
});

async function findAvailablePort(startPort: number, maxAttempts = 20): Promise<number> {
  for (let offset = 0; offset < maxAttempts; offset += 1) {
    const port = startPort + offset;
    const available = await new Promise<boolean>((resolve) => {
      const server = net.createServer();
      server.once("error", () => resolve(false));
      server.once("listening", () => {
        server.close(() => resolve(true));
      });
      server.listen(port, "0.0.0.0");
    });
    if (available) return port;
  }
  throw new Error(`No available port found in range ${startPort}-${startPort + maxAttempts - 1}`);
}

function writeFrontendEnv(port: number) {
  const envPath = path.resolve(process.cwd(), "../frontend/.env.local");
  const content = `VITE_API_BASE_URL=http://localhost:${port}\n`;
  try {
    fs.writeFileSync(envPath, content);
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    console.warn(`Failed to write frontend env file: ${message}`);
  }
}

const port = await findAvailablePort(desiredPort);
if (process.env.NODE_ENV !== "production") {
  writeFrontendEnv(port);
}

app.listen(port, () => {
  console.log(`Backend listening on http://localhost:${port}`);
});
