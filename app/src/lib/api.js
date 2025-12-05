const BASE_URL =
  process.env.REACT_APP_API_BASE_URL || 'https://truthlens-api-276376440888.us-central1.run.app';
const MASTER_KEY = process.env.REACT_APP_MASTER_KEY || '';
const STORAGE_KEY = 'pramana_api_key';

const requireApiKey = () => {
  const key = getStoredApiKey() || MASTER_KEY;
  if (!key) {
    throw new Error(
      'API key missing. Generate a key in the console or set REACT_APP_MASTER_KEY in your .env.local.'
    );
  }
  return key;
};

export const getStoredApiKey = () => {
  try {
    return window.localStorage.getItem(STORAGE_KEY) || '';
  } catch (err) {
    console.error('Unable to read localStorage', err);
    return '';
  }
};

export const storeApiKey = (key) => {
  try {
    window.localStorage.setItem(STORAGE_KEY, key);
  } catch (err) {
    console.error('Unable to persist API key', err);
  }
};

const fetchWithAuth = async (path, options = {}) => {
  const apiKey = requireApiKey();
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
    Authorization: `Bearer ${apiKey}`,
  };

  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Request failed with status ${response.status}`);
  }

  return response.json();
};

export const registerApiKey = async ({ email, validityDays }) => {
  requireApiKey();
  const payload = {};
  if (email) payload.email = email;
  if (validityDays) payload.valid_for_days = validityDays;

  const result = await fetchWithAuth('/v1/register_key', {
    method: 'POST',
    body: JSON.stringify(payload),
  });

  if (result?.api_key) {
    storeApiKey(result.api_key);
  }
  return result;
};

export const verifyClaim = async ({ text, mode = 'fast', language = 'en', image }) => {
  const apiKey = requireApiKey();

  const formData = new FormData();
  if (text) formData.append('text', text);
  formData.append('mode', mode);
  formData.append('language', language);
  if (image) formData.append('image', image);

  const response = await fetch(`${BASE_URL}/v1/verify`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${apiKey}`,
    },
    body: formData,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Verification failed (${response.status})`);
  }

  return response.json();
};

export const verifyUrl = async ({ url }) => {
  const result = await fetchWithAuth('/v1/verify_url', {
    method: 'POST',
    body: JSON.stringify({ url }),
  });
  return result;
};

export const fetchTrendingClaims = async ({ limit = 5, language = 'en' } = {}) => {
  const result = await fetchWithAuth('/v1/auto_scan', {
    method: 'POST',
    body: JSON.stringify({ limit, language }),
  });
  return result;
};
