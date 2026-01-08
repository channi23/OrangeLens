import { Link, Route, Routes } from "react-router-dom";
import ListPage from "./pages/ListPage";
import CreatePage from "./pages/CreatePage";
import EditPage from "./pages/EditPage";
import DetailPage from "./pages/DetailPage";

export default function App() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
          <div>
            <Link to="/" className="text-xl font-semibold tracking-tight">
              Pramana Testing Suite
            </Link>
            <p className="text-sm text-slate-500">CRUD + Verification playground</p>
          </div>
          <nav className="flex items-center gap-4 text-sm">
            <Link className="text-slate-600 hover:text-slate-900" to="/">
              Posts
            </Link>
            <Link className="rounded-md bg-slate-900 px-3 py-2 text-white" to="/create">
              New Post
            </Link>
          </nav>
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl px-6 py-8">
        <Routes>
          <Route path="/" element={<ListPage />} />
          <Route path="/create" element={<CreatePage />} />
          <Route path="/edit/:id" element={<EditPage />} />
          <Route path="/posts/:id" element={<DetailPage />} />
        </Routes>
      </main>
    </div>
  );
}
