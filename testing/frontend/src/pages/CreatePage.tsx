import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { createPost } from "../lib/api";
import VerificationPanel from "../components/VerificationPanel";
import type { Post } from "../lib/api";

export default function CreatePage() {
  const navigate = useNavigate();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [image, setImage] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [created, setCreated] = useState<Post | null>(null);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setSubmitting(true);

    const formData = new FormData();
    formData.append("title", title);
    formData.append("description", description);
    if (image) {
      formData.append("image", image);
    }

    const post = await createPost(formData);
    setCreated(post);
    setSubmitting(false);
  };

  return (
    <div className="space-y-6">
      <form onSubmit={handleSubmit} className="rounded-xl border border-slate-200 bg-white p-6">
        <div className="grid gap-4">
          <div>
            <label className="text-sm font-semibold text-slate-700">Title</label>
            <input
              className="mt-2 w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:border-slate-400 focus:outline-none"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Enter a headline"
              required
            />
          </div>
          <div>
            <label className="text-sm font-semibold text-slate-700">Description</label>
            <textarea
              className="mt-2 w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:border-slate-400 focus:outline-none"
              rows={5}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe the claim"
              required
            />
          </div>
          <div>
            <label className="text-sm font-semibold text-slate-700">Image (optional)</label>
            <input
              type="file"
              accept="image/*"
              className="mt-2 block w-full text-sm text-slate-500"
              onChange={(e) => setImage(e.target.files?.[0] || null)}
            />
          </div>
        </div>
        <div className="mt-6 flex items-center gap-3">
          <button
            type="submit"
            className="rounded-md bg-slate-900 px-4 py-2 text-sm font-semibold text-white"
            disabled={submitting}
          >
            {submitting ? "Creating..." : "Create & Verify"}
          </button>
          <button
            type="button"
            className="rounded-md border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-600"
            onClick={() => navigate("/")}
          >
            Cancel
          </button>
        </div>
      </form>

      {created && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Verification Result</h2>
            <button
              className="text-sm text-blue-600 hover:underline"
              onClick={() => navigate(`/posts/${created.id}`)}
            >
              View details
            </button>
          </div>
          <VerificationPanel verification={created.verification || undefined} />
        </div>
      )}
    </div>
  );
}
