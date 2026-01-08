import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { fetchPost, updatePost } from "../lib/api";
import VerificationPanel from "../components/VerificationPanel";
import type { Post } from "../lib/api";

export default function EditPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [post, setPost] = useState<Post | null>(null);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [image, setImage] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!id) return;
    fetchPost(id).then((data) => {
      setPost(data);
      setTitle(data.title);
      setDescription(data.description);
    });
  }, [id]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!id) return;
    setSubmitting(true);

    const formData = new FormData();
    formData.append("title", title);
    formData.append("description", description);
    if (image) {
      formData.append("image", image);
    }

    const updated = await updatePost(id, formData);
    setPost(updated);
    setSubmitting(false);
  };

  if (!post) {
    return <p className="text-sm text-slate-500">Loading post...</p>;
  }

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
              required
            />
          </div>
          <div>
            <label className="text-sm font-semibold text-slate-700">Replace image (optional)</label>
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
            {submitting ? "Saving..." : "Save & Verify"}
          </button>
          <button
            type="button"
            className="rounded-md border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-600"
            onClick={() => navigate("/")}
          >
            Back
          </button>
        </div>
      </form>

      {post.verification && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold">Latest Verification</h2>
          <VerificationPanel verification={post.verification} />
        </div>
      )}
    </div>
  );
}
