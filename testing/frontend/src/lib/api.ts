import axios from "axios";

export const backendUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:5000";

export const api = axios.create({
  baseURL: `${backendUrl}/api`,
});

export type Verification = {
  verdict?: string;
  truth_score?: number;
  truthScore?: number;
  confidence?: string;
  explanation?: string;
  citations?: Array<{ title?: string; url?: string } | string>;
  cached?: boolean;
};

export type Post = {
  id: string;
  title: string;
  description: string;
  imagePath?: string | null;
  createdAt: string;
  updatedAt: string;
  verification?: Verification | null;
  verdict?: string | null;
  truthScore?: number | null;
  confidence?: string | null;
  explanation?: string | null;
};

export async function fetchPosts() {
  const { data } = await api.get<Post[]>("/posts");
  return data;
}

export async function fetchPost(id: string) {
  const { data } = await api.get<Post>(`/posts/${id}`);
  return data;
}

export async function createPost(formData: FormData) {
  const { data } = await api.post<Post>("/posts", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function updatePost(id: string, formData: FormData) {
  const { data } = await api.put<Post>(`/posts/${id}`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function deletePost(id: string) {
  await api.delete(`/posts/${id}`);
}

export async function verifyPost(id: string) {
  const { data } = await api.post<Post>(`/posts/${id}/verify`);
  return data;
}
