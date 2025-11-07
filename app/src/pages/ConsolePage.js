import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  getStoredApiKey,
  registerApiKey,
  verifyClaim,
  verifyUrl,
  storeApiKey,
  fetchTrendingClaims,
} from '../lib/api';
import { getCachedResults, storeResult } from '../lib/cache';

// Static constants moved outside of component
export const validityOptions = [
  { label: '7 days', value: 7 },
  { label: '30 days', value: 30 },
  { label: '60 days', value: 60 },
  { label: '90 days', value: 90 },
];

export const tabs = [
  { id: 'text', label: 'Text' },
  { id: 'image', label: 'Image' },
  { id: 'url', label: 'URL' },
];

export const verdictColors = {
  true: 'bg-white/10 text-white border border-white/30',
  false: 'bg-white/5 text-zinc-300 border border-white/20',
  misleading: 'bg-white/5 text-zinc-300 border border-white/20',
  unknown: 'bg-white/5 text-zinc-400 border border-white/20',
  error: 'bg-white/5 text-zinc-400 border border-white/20',
};

const ConsolePage = () => {
  const [apiKey, setApiKey] = useState('');
  const [validity, setValidity] = useState(validityOptions[1].value);
  const [registerStatus, setRegisterStatus] = useState('');
  const [registerLoading, setRegisterLoading] = useState(false);

  const [activeTab, setActiveTab] = useState('text');
  const [claimText, setClaimText] = useState('');
  const [claimUrl, setClaimUrl] = useState('');
  const [imageFile, setImageFile] = useState(null);

  const [verifyLoading, setVerifyLoading] = useState(false);
  const [verifyError, setVerifyError] = useState('');
  const [result, setResult] = useState(null);
  const [recentResults, setRecentResults] = useState([]);
  const [trendingClaims, setTrendingClaims] = useState([]);

  useEffect(() => {
    setApiKey(getStoredApiKey());
    setRecentResults(getCachedResults());
    const loadTrending = async () => {
      try {
        const res = await fetchTrendingClaims({ limit: 5, language: 'en' });
        if (res?.summary?.results?.length) {
          setTrendingClaims(res.summary.results);
        }
      } catch (err) {
        console.error('Trending fetch failed', err);
      }
    };
    loadTrending();
  }, []);

  useEffect(() => {
    setVerifyError('');
    setResult(null);
  }, [activeTab]);

  const handleRegister = async (event) => {
    event.preventDefault();
    setRegisterStatus('');
    setRegisterLoading(true);
    try {
      const response = await registerApiKey({
        validityDays: Number(validity) || undefined,
      });
      const key = response?.data?.api_key || response?.api_key;
      if (key) {
        setApiKey(key);
        storeApiKey(key);
        setRegisterStatus(
          `API key generated successfully. Expires in ${response?.data?.valid_days || validity} days.`
        );
      } else {
        setRegisterStatus('API key created, but no key returned.');
      }
    } catch (error) {
      setRegisterStatus(error.message || 'Failed to provision API key.');
    } finally {
      setRegisterLoading(false);
    }
  };

  const handleFileChange = (event) => {
    const file = event.target.files?.[0];
    if (file) {
      // File size validation (max 5MB)
      const maxSize = 5 * 1024 * 1024;
      if (file.size > maxSize) {
        setVerifyError('Image must be less than 5MB.');
        setImageFile(null);
        return;
      }
      // File type validation (must be image)
      if (!file.type.startsWith('image/')) {
        setVerifyError('Only image files are allowed.');
        setImageFile(null);
        return;
      }
      setVerifyError('');
      setImageFile(file);
    } else {
      setImageFile(null);
    }
  };

  const citations = useMemo(() => {
    if (!result?.citations) return [];
    if (Array.isArray(result.citations)) {
      return result.citations.map((item) => {
        if (typeof item === 'string') {
          return { title: item, url: item };
        }
        return {
          title: item.title || item.url || 'Source',
          url: item.url || '#',
        };
      });
    }
    return [];
  }, [result]);

  const handleVerify = async (event) => {
    event.preventDefault();
    setVerifyLoading(true);
    setVerifyError('');
    try {
      let payload;
      let data;
      const isURL = activeTab === 'url';
      const isImage = activeTab === 'image';
      if (isURL) {
        if (!claimUrl.trim()) throw new Error('Enter a URL to verify.');
        let urlInput = claimUrl.trim().replace(/\s+/g, '');

        // --- Normalize URL, prevent double https:// and www. ---
        let workingUrl = urlInput;
        // Remove all leading protocols for normalization
        workingUrl = workingUrl.replace(/^(https?:\/\/)+/i, '');
        // Remove all leading www.'s (could be multiple)
        workingUrl = workingUrl.replace(/^(www\.)+/i, '');

        // Add protocol back
        workingUrl = 'https://' + workingUrl;

        let parsed;
        let parsedHost = '';
        try {
          parsed = new URL(workingUrl);
          parsedHost = parsed.hostname;
        } catch {
          // fallback: try to add .com if missing, then parse
          let hostPart = workingUrl.replace(/^https?:\/\//, '').split('/')[0];
          // Add .com if no TLD
          if (!/\.[a-z]{2,}$/i.test(hostPart)) {
            hostPart += '.com';
          }
          // Add www. if missing and not a subdomain
          if (!/^www\./i.test(hostPart) && !hostPart.match(/^[a-z0-9-]+\.[a-z]{2,}/i)?.[0]?.includes('.')) {
            hostPart = 'www.' + hostPart;
          }
          // Rebuild
          let pathPart = '';
          const idx = workingUrl.indexOf('/');
          if (idx !== -1) {
            pathPart = workingUrl.slice(workingUrl.indexOf('/', workingUrl.indexOf('//') + 2));
          }
          workingUrl = 'https://' + hostPart + pathPart;
          try {
            parsed = new URL(workingUrl);
            parsedHost = parsed.hostname;
          } catch {
            throw new Error('Invalid or incomplete URL. Please check your input.');
          }
        }

        // Step 3: Ensure TLD and www present (again, but prevent double www.)
        if (!/\.[a-z]{2,}$/i.test(parsedHost)) {
          parsedHost += '.com';
        }
        if (!/^www\./i.test(parsedHost) && /^[a-z0-9-]+\.[a-z]{2,}(?:\/|$)/i.test(parsedHost + '/')) {
          parsedHost = 'www.' + parsedHost;
        }
        // Remove any double www. (e.g., www.www.site.com)
        parsedHost = parsedHost.replace(/^(www\.){2,}/i, 'www.');
        // Reconstruct final normalized url
        let finalUrl = parsed.protocol + '//' + parsedHost + parsed.pathname + parsed.search + parsed.hash;
        // Validate
        try {
          new URL(finalUrl);
        } catch {
          throw new Error('Invalid or incomplete URL. Please check your input.');
        }

        // Log for debugging
        console.log('[Verify] Final normalized URL:', finalUrl);

        setClaimText(''); // Clear claim text when verifying URL
        try {
          data = await verifyUrl({ url: finalUrl });
          // Log backend response for debugging
          console.log('[Verify] Backend response:', data);
        } catch (err) {
          // Try to extract error message from backend
          let msg = 'Verification failed.';
          if (err?.response?.data) {
            msg = err.response.data.message || JSON.stringify(err.response.data);
          } else if (err?.message) {
            msg = err.message;
          }
          setVerifyError(msg);
          setResult(null);
          return;
        }
        // Explicitly check for response structure
        if (!data || typeof data !== 'object' || !('verdict' in data)) {
          console.error('[Verify] Server returned no valid verdict. Full response:', data);
          setVerifyError('Server returned no valid verdict — please check URL format or retry.');
          setResult(null);
          return;
        }
      } else {
        if (isImage) {
          if (!imageFile) throw new Error('Upload an image to verify.');
          payload = claimText.trim()
            ? { image: imageFile, text: claimText.trim() }
            : { image: imageFile };
        } else {
          if (!claimText.trim()) throw new Error('Enter text to verify.');
          payload = { text: claimText.trim() };
        }
        try {
          data = await verifyClaim(payload);
          // Log backend response for debugging
          console.log('[Verify] Backend response:', data);
        } catch (err) {
          let msg = 'Verification failed.';
          if (err?.response?.data) {
            msg = err.response.data.message || JSON.stringify(err.response.data);
          } else if (err?.message) {
            msg = err.message;
          }
          setVerifyError(msg);
          setResult(null);
          return;
        }
        if (!data || typeof data !== 'object' || !('verdict' in data)) {
          console.error('[Verify] Server returned no valid verdict. Full response:', data);
          setVerifyError('Server returned no valid verdict — please check your input or retry.');
          setResult(null);
          return;
        }
      }

      setResult(data);
      const cached = storeResult({
        ...data,
        stored_at: new Date().toISOString(),
      });
      setRecentResults(cached);
    } catch (error) {
      console.error(error);
      setVerifyError(error.message || 'Verification failed.');
      setResult(null);
    } finally {
      setVerifyLoading(false);
    }
  };

  const copyToClipboard = async (value) => {
    if (!value) return;
    try {
      await navigator.clipboard.writeText(value);
      setRegisterStatus('Copied to clipboard.');
    } catch (error) {
      console.error('Clipboard copy failed', error);
      setRegisterStatus('Clipboard not available.');
    }
  };

  const activeVerdict = (result?.verdict || '').toLowerCase();
  const verdictBadgeClass = verdictColors[activeVerdict] || verdictColors.unknown;

  // For API key show/hide
  const [showApiKey, setShowApiKey] = useState(false);

  return (
    <div className="min-h-screen text-black bg-gradient-to-b from-white via-indigo-50 via-purple-100 to-purple-200">
      {/* Subtle Background Gradient */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.05),transparent_60%)] pointer-events-none" />
      
      <div className="relative z-10 flex min-h-screen flex-col">
        {/* Header */}
        <header className="flex items-center justify-between border-b border-purple-200/50 px-6 py-5 md:px-10 backdrop-blur-sm">
          <Link
            to="/"
            className="group flex items-center gap-2 text-sm text-zinc-400 transition-colors duration-300 hover:text-gray-900"
          >
            <svg
              className="h-4 w-4 transition-transform duration-300 group-hover:-translate-x-1"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Back to landing
          </Link>
          <div className="flex items-center gap-2 text-xs text-zinc-500">
            <span>Need help?</span>
            <a
              href="mailto:orangexai@gmail.com"
              className="font-medium text-gray-900 underline decoration-purple-200/50 underline-offset-4 transition-all duration-300 hover:decoration-purple-400"
            >
              orangexai@gmail.com
            </a>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex flex-1 flex-col gap-8 px-6 py-10 md:flex-row md:px-10">
          {/* Sidebar */}
          <section className="w-full space-y-6 md:w-1/3">
            {/* API Key Generation */}
            <div className="group rounded-2xl border border-purple-200/50 bg-white/40 backdrop-blur-sm p-6 transition-all duration-300 hover:border-purple-200/50 hover:bg-white/60">
              <div className="mb-1 flex items-center gap-2">
                <div className="h-1 w-1 rounded-full bg-purple-400" />
                <h2 className="text-base font-semibold text-gray-900">API Key Provisioning</h2>
              </div>
              <p className="mt-2 text-xs leading-relaxed text-zinc-500">
                Generate a trial key to integrate Pramana into your workflow.
              </p>

              <form className="mt-6 space-y-4" onSubmit={handleRegister}>
                <div>
                  <label
                    htmlFor="validity"
                    className="block text-[13px] font-semibold text-[#4C3C78] tracking-wide mb-1"
                  >
                    Validity Period
                  </label>
                  <div className="relative mt-3">
                    <select
                      id="validity"
                      value={validity}
                      onChange={(event) => setValidity(Number(event.target.value))}
                      className="mt-3 w-full appearance-none rounded-lg border border-[#D6C6E8] bg-gradient-to-r from-[#F9F8FC] to-[#F4F0FA] px-4 py-3 text-[14px] text-gray-800 font-medium shadow-sm outline-none transition-all duration-300 focus:border-[#7E57C2] focus:ring-2 focus:ring-[#B39DDB]/50 hover:border-[#9575CD] hover:shadow-md"
                    >
                      {validityOptions.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                    <span className="absolute right-4 top-1/2 -translate-y-1/2 text-[#7E57C2] pointer-events-none">
                      ▼
                    </span>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={registerLoading}
                  className="w-full rounded-2xl bg-gradient-to-r from-[#5B4B8A] via-[#7D5BA6] to-[#A888C1] text-white px-4 py-3 text-[15px] font-semibold tracking-wide shadow-md transition-all duration-300 hover:shadow-lg hover:brightness-110 active:scale-[0.98] disabled:cursor-wait disabled:opacity-60"
                >
                  {registerLoading ? 'Generating...' : 'Generate Key'}
                </button>
              </form>

              {registerStatus && (
                <div className="mt-4 rounded-xl border border-purple-200/50 bg-white/40 px-4 py-3 text-xs leading-relaxed text-zinc-600">
                  {registerStatus}
                </div>
              )}

              {apiKey && (
                <div className="mt-5 space-y-2">
                  <div className="flex items-center justify-between text-[11px] text-zinc-500">
                    <span className="font-medium uppercase tracking-wider">Your API Key</span>
                    <div className="flex items-center gap-3">
                      <button
                        type="button"
                        onClick={() => setShowApiKey((v) => !v)}
                        aria-label={showApiKey ? "Hide API Key" : "Show API Key"}
                        className="text-gray-900 underline decoration-purple-200/50 underline-offset-2 transition-all duration-300 hover:decoration-purple-400"
                      >
                        {showApiKey ? "Hide" : "Show"}
                      </button>
                      <button
                        type="button"
                        onClick={() => copyToClipboard(apiKey)}
                        aria-label="Copy API Key"
                        className="text-gray-900 underline decoration-purple-200/50 underline-offset-2 transition-all duration-300 hover:decoration-purple-400"
                      >
                        Copy
                      </button>
                    </div>
                  </div>
                  <div
                    className="rounded-xl border border-purple-200/50 bg-purple-100/80 px-4 py-3 font-mono text-xs text-gray-900 select-all overflow-x-auto whitespace-pre-wrap break-all"
                    style={{ wordBreak: 'break-all', whiteSpace: 'pre-wrap', maxHeight: '5rem' }}
                  >
                    {showApiKey ? apiKey : '•'.repeat(Math.max(apiKey.length, 8))}
                  </div>
                </div>
              )}
            </div>

            {/* Recent Results */}
            <div className="rounded-2xl border border-purple-200/50 bg-white/40 p-6 backdrop-blur-sm">
              <div className="mb-1 flex items-center gap-2">
                <div className="h-1 w-1 rounded-full bg-purple-400/60" />
                <h3 className="text-sm font-semibold text-gray-900">Recent Verifications</h3>
              </div>
              <p className="mt-2 text-xs text-zinc-500">
                Cached locally — clears when you reset your browser.
              </p>
              <div className="mt-4 space-y-3">
                {recentResults.length === 0 && (
                  <p className="text-xs text-zinc-600">No verifications yet.</p>
                )}
                {recentResults.map((entry) => (
                  <div
                    key={entry.request_id || entry.stored_at}
                    className="group rounded-xl border border-purple-200/50 bg-purple-100/50 p-4 transition-all duration-300 hover:border-purple-200/50 hover:bg-purple-100/80"
                  >
                    <div className="flex items-center justify-between text-[10px] font-medium uppercase tracking-wider text-zinc-500">
                      <span>{(entry.verdict || 'Unknown').toUpperCase()}</span>
                      <span>
                        {entry.metrics?.latency_ms ? `${Math.round(entry.metrics.latency_ms)}ms` : '—'}
                      </span>
                    </div>
                    <p className="mt-2 line-clamp-2 text-xs leading-relaxed text-zinc-500">
                      {entry.explanation || entry.claim_text || 'No explanation provided.'}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* Trending Claims */}
            <div className="rounded-2xl border border-purple-200/50 bg-white/40 p-6 backdrop-blur-sm mt-8">
              <div className="mb-1 flex items-center gap-2">
                <div className="h-1 w-1 rounded-full bg-purple-400/60" />
                <h3 className="text-sm font-semibold text-gray-900">Trending Misinformation</h3>
              </div>
              <p className="mt-2 text-xs text-zinc-500">
                Top false or misleading claims detected automatically.
              </p>
              <div className="mt-4 space-y-3">
                {trendingClaims.length === 0 && (
                  <p className="text-xs text-zinc-600">No trending claims yet.</p>
                )}
                {trendingClaims.map((claim, i) => (
                  <div
                    key={claim.request_id || i}
                    className="group rounded-xl border border-purple-200/50 bg-purple-100/50 p-4 transition-all duration-300 hover:border-purple-200/50 hover:bg-purple-100/80"
                  >
                    <div className="flex items-center justify-between text-[10px] font-medium uppercase tracking-wider text-zinc-500">
                      <span>{(claim.verdict || 'Unknown').toUpperCase()}</span>
                      <span>{claim.confidence ? `${Math.round(claim.confidence * 100)}%` : '—'}</span>
                    </div>
                    <p className="mt-2 line-clamp-2 text-xs leading-relaxed text-zinc-500">
                      {claim.text || claim.explanation || 'No description available.'}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </section>

          {/* Main Verification Area */}
          <section className="w-full md:w-2/3">
            <div className="rounded-2xl border border-purple-200/50 bg-white/40 p-6 backdrop-blur-sm md:p-8">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div className="flex items-center gap-2">
                  <div className="h-1 w-1 rounded-full bg-purple-400" />
                  <h2 className="text-base font-semibold text-gray-900">Verify Claim</h2>
                </div>

                {/* Tab Switcher */}
                <div className="flex gap-1 rounded-xl border border-[#D6C6E8]/60 bg-[#F6F3FA]/70 p-1 shadow-sm backdrop-blur-sm">
                  {tabs.map((tab) => (
                    <button
                      key={tab.id}
                      type="button"
                      onClick={() => setActiveTab(tab.id)}
                      className={`rounded-lg px-4 py-1.5 text-xs font-medium transition-all duration-300 ${
                        activeTab === tab.id
                          ? 'bg-gradient-to-r from-[#5B4B8A] via-[#7D5BA6] to-[#A888C1] text-white shadow-md'
                          : 'text-[#6E5A94] hover:bg-[#E9E3F2] hover:text-[#4C3C78]'
                      }`}
                    >
                      {tab.label}
                    </button>
                  ))}
                </div>
              </div>

              <form className="mt-8 space-y-5" onSubmit={handleVerify}>
                {activeTab === 'text' && (
                  <div>
                    <label
                      htmlFor="claim"
                      className="block text-[11px] font-medium uppercase tracking-wider text-zinc-500"
                    >
                      Claim Text
                    </label>
                    <textarea
                      id="claim"
                      rows="5"
                      placeholder="Enter the claim your team needs to verify..."
                      value={claimText}
                      onChange={(event) => setClaimText(event.target.value)}
                      className="mt-2 w-full rounded-xl border border-purple-200/50 bg-purple-50/60 px-4 py-3 text-sm leading-relaxed text-gray-900 placeholder:text-zinc-500 outline-none transition-all duration-300 focus:border-purple-300 focus:bg-purple-100/80"
                    />
                  </div>
                )}

                {activeTab === 'image' && (
                  <>
                    <div>
                      <label
                        htmlFor="image"
                        className="block text-[11px] font-medium uppercase tracking-wider text-zinc-500"
                      >
                        Evidence Image
                      </label>
                      <input
                        id="image"
                        type="file"
                        accept="image/*"
                        onChange={handleFileChange}
                        className="mt-2 w-full cursor-pointer rounded-xl border border-dashed border-purple-200/50 bg-purple-50/60 px-4 py-6 text-sm text-zinc-500 outline-none transition-all duration-300 file:mr-4 file:cursor-pointer file:rounded-lg file:border-0 file:bg-white file:px-4 file:py-2 file:text-xs file:font-semibold file:text-black hover:border-purple-200/50 hover:bg-purple-100/80"
                      />
                    </div>
                    <div className="mt-4">
                      <label htmlFor="imageClaim" className="block text-[11px] font-medium uppercase tracking-wider text-zinc-500">
                        Optional Context
                      </label>
                      <textarea
                        id="imageClaim"
                        rows="3"
                        placeholder="(Optional) Add context about the image…"
                        value={claimText}
                        onChange={(event) => setClaimText(event.target.value)}
                        className="mt-2 w-full rounded-xl border border-purple-200/50 bg-purple-50/60 px-4 py-2.5 text-sm leading-relaxed text-gray-900 placeholder:text-zinc-500 outline-none transition-all duration-300 focus:border-purple-300 focus:bg-purple-100/80"
                      />
                    </div>
                  </>
                )}

                {activeTab === 'url' && (
                  <div>
                    <label
                      htmlFor="url"
                      className="block text-[11px] font-medium uppercase tracking-wider text-zinc-500"
                    >
                      URL to Verify
                    </label>
                    <input
                      id="url"
                      type="text"
                      placeholder="Enter a URL (any format: google.com, bbc.in/news, http://…)"
                      value={claimUrl}
                      onChange={(event) => setClaimUrl(event.target.value)}
                      className="mt-2 w-full rounded-xl border border-purple-200/50 bg-purple-50/60 px-4 py-2.5 text-sm text-gray-900 placeholder:text-zinc-500 outline-none transition-all duration-300 focus:border-purple-300 focus:bg-purple-100/80"
                    />
                    <p className="mt-2 text-[11px] text-zinc-500">We accept any format — e.g., google.com, bbc.in/news, http://site.org. We’ll normalize it automatically.</p>
                  </div>
                )}

                <button
                  type="submit"
                  disabled={verifyLoading}
                  className="w-full rounded-2xl bg-gradient-to-r from-[#4C3C78] via-[#6E4FA2] to-[#A87BCB] text-white px-5 py-3 text-[15px] font-semibold tracking-wide shadow-md transition-all duration-300 hover:shadow-lg hover:brightness-110 active:scale-[0.98] disabled:cursor-wait disabled:opacity-60"
                >
                  {verifyLoading ? 'Verifying...' : 'Run Verification'}
                </button>
              </form>

              {verifyError && (
                <div className="mt-6 rounded-xl border border-purple-200/50 bg-white/40 px-4 py-3 text-sm text-zinc-600">
                  {verifyError}
                </div>
              )}

              {result && !verifyError && (
                <div className="mt-8 space-y-6">
                  {/* Verdict Badge */}
                  <div
                    className={`inline-flex items-center gap-2 rounded-full px-4 py-2 text-[11px] font-semibold uppercase tracking-wider backdrop-blur-sm ${verdictBadgeClass.replace(/bg-white\/10|bg-white\/5|border-white\/30|border-white\/20|border-white\/10|text-white/g, 'bg-purple-100/80 border-purple-200/50 text-gray-900')}`}
                  >
                    <div className="h-1.5 w-1.5 rounded-full bg-current" />
                    <span>Verdict: {(result.verdict || 'Unknown').toUpperCase()}</span>
                  </div>

                  {/* Results Grid */}
                  <div className="grid gap-5 md:grid-cols-2">
                    {/* Confidence Card */}
                    <div className="group rounded-xl border border-purple-200/50 bg-purple-100/50 p-5 transition-all duration-300 hover:border-purple-200/50 hover:bg-purple-100/80">
                      <p className="text-[11px] font-medium uppercase tracking-wider text-zinc-500">
                        Confidence Score
                      </p>
                      <p className="mt-3 text-3xl font-bold text-gray-900">
                        {result.confidence != null ? `${Math.round(result.confidence * 100)}%` : '—'}
                      </p>
                      <p className="mt-4 text-sm leading-relaxed text-zinc-500">
                        {result.explanation || 'No explanation provided.'}
                      </p>
                    </div>

                    {/* Performance Card */}
                    <div className="group rounded-xl border border-purple-200/50 bg-purple-100/50 p-5 transition-all duration-300 hover:border-purple-200/50 hover:bg-purple-100/80">
                      <p className="text-[11px] font-medium uppercase tracking-wider text-zinc-500">
                        Performance Metrics
                      </p>
                      <div className="mt-4 space-y-3 text-sm text-zinc-500">
                        <div className="flex items-center justify-between border-b border-purple-200/50 pb-2">
                          <span className="text-zinc-500">Latency</span>
                          <span className="font-semibold text-gray-900">
                            {result.metrics?.latency_ms ? `${Math.round(result.metrics.latency_ms)}ms` : '—'}
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-zinc-500">Cost</span>
                          <span className="font-semibold text-gray-900">
                            {result.metrics?.cost_usd != null ? `$${result.metrics.cost_usd.toFixed(4)}` : '—'}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Citations */}
                  {citations.length > 0 && (
                    <div className="rounded-xl border border-purple-200/50 bg-purple-100/50 p-5">
                      <p className="text-[11px] font-medium uppercase tracking-wider text-zinc-500">
                        Source Citations
                      </p>
                      <ul className="mt-4 space-y-2.5">
                        {citations.map((citation, index) => (
                          <li key={`${citation.url}-${index}`} className="flex items-start gap-2 text-sm">
                            <span className="mt-1 h-1 w-1 flex-shrink-0 rounded-full bg-purple-400/40" />
                            <a
                              href={citation.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-zinc-500 underline decoration-purple-200/50 underline-offset-2 transition-all duration-300 hover:text-gray-900 hover:decoration-purple-400"
                            >
                              {citation.title}
                            </a>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          </section>
        </main>
      </div>
    </div>
  );
};

export default ConsolePage;
