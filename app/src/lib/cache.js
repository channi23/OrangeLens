const CACHE_KEY = 'pramana_recent_results';
const MAX_ITEMS = 10;

const readCache = () => {
  try {
    const raw = window.localStorage.getItem(CACHE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (err) {
    console.error('Failed to parse cache', err);
    return [];
  }
};

const writeCache = (items) => {
  try {
    window.localStorage.setItem(CACHE_KEY, JSON.stringify(items.slice(0, MAX_ITEMS)));
  } catch (err) {
    console.error('Failed to persist cache', err);
  }
};

export const getCachedResults = () => readCache();

export const storeResult = (entry) => {
  const items = readCache();
  const next = [entry, ...items.filter((item) => item.request_id !== entry.request_id)];
  writeCache(next);
  return next;
};
