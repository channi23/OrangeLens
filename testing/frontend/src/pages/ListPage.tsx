import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { backendUrl, deletePost, fetchPosts, verifyPost } from "../lib/api";
import type { Post } from "../lib/api";
import VerdictBadge from "../components/VerdictBadge";

export default function ListPage() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    const data = await fetchPosts();
    setPosts(data);
    setLoading(false);
  };

  useEffect(() => {
    load();
  }, []);

  const handleDelete = async (id: string) => {
    setBusyId(id);
    await deletePost(id);
    await load();
    setBusyId(null);
  };

  const handleVerify = async (id: string) => {
    setBusyId(id);
    await verifyPost(id);
    await load();
    setBusyId(null);
  };

  if (loading) {
    return <p className="text-sm text-slate-500">Loading posts...</p>;
  }

  return (
    <div className="space-y-6">
      {posts.length === 0 && (
        <div className="rounded-lg border border-dashed border-slate-200 bg-white p-6 text-center text-sm text-slate-500">
          No posts yet. Create one to see verification details.
        </div>
      )}

      {posts.map((post) => {
        const verification = post.verification;
        const truthScore =
          typeof verification?.truth_score === "number"
            ? verification?.truth_score
            : post.truthScore ?? undefined;
        const verdict = verification?.verdict || post.verdict;
        const cached = verification?.cached;

        return (
          <article key={post.id} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <VerdictBadge verdict={verdict} />
                  {truthScore !== undefined && (
                    <span className="text-xs text-slate-500">Truth Score: {truthScore.toFixed(2)}</span>
                  )}
                  {verification?.confidence && (
                    <span className="text-xs text-slate-500">Confidence: {verification.confidence}</span>
                  )}
                  {cached !== undefined && (
                    <span className="text-xs text-slate-500">Cached: {cached ? "true" : "false"}</span>
                  )}
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-slate-900">{post.title}</h3>
                  <p className="mt-1 text-sm text-slate-600">{post.description}</p>
                </div>
                <div className="flex flex-wrap gap-3">
                  <Link className="text-sm text-blue-600 hover:underline" to={`/posts/${post.id}`}>
                    View details
                  </Link>
                  <Link className="text-sm text-slate-600 hover:text-slate-900" to={`/edit/${post.id}`}>
                    Edit
                  </Link>
                </div>
              </div>
              <div className="flex flex-col items-end gap-3">
                {post.imagePath && (
                  <img
                    src={`${backendUrl}${post.imagePath}`}
                    alt={post.title}
                    className="h-24 w-24 rounded-lg object-cover"
                  />
                )}
                <div className="flex gap-2">
                  <button
                    className="rounded-md border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-600 hover:border-slate-400"
                    onClick={() => handleVerify(post.id)}
                    disabled={busyId === post.id}
                  >
                    Verify Now
                  </button>
                  <button
                    className="rounded-md border border-rose-200 px-3 py-1 text-xs font-semibold text-rose-600 hover:border-rose-400"
                    onClick={() => handleDelete(post.id)}
                    disabled={busyId === post.id}
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          </article>
        );
      })}
    </div>
  );
}
