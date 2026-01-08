import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { backendUrl, fetchPost } from "../lib/api";
import type { Post } from "../lib/api";
import VerificationPanel from "../components/VerificationPanel";

export default function DetailPage() {
  const { id } = useParams();
  const [post, setPost] = useState<Post | null>(null);

  useEffect(() => {
    if (!id) return;
    fetchPost(id).then(setPost);
  }, [id]);

  if (!post) {
    return <p className="text-sm text-slate-500">Loading details...</p>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold">{post.title}</h2>
          <p className="text-sm text-slate-500">Post ID: {post.id}</p>
        </div>
        <Link className="text-sm text-blue-600 hover:underline" to={`/edit/${post.id}`}>
          Edit post
        </Link>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-6">
        <p className="text-sm text-slate-600">{post.description}</p>
        {post.imagePath && (
          <img
            src={`${backendUrl}${post.imagePath}`}
            alt={post.title}
            className="mt-4 max-h-80 w-full rounded-lg object-cover"
          />
        )}
      </div>

      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Verification Summary</h3>
        <VerificationPanel verification={post.verification || undefined} />
      </div>

      <div className="space-y-3">
        <h3 className="text-lg font-semibold">Raw Verification JSON</h3>
        <pre className="max-h-[420px] overflow-auto rounded-lg border border-slate-200 bg-slate-900 p-4 text-xs text-slate-100">
          {JSON.stringify(post.verification || {}, null, 2)}
        </pre>
      </div>
    </div>
  );
}
