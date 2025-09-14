import React, { useState, useEffect } from 'react';
import './App.css';

const API_BASE_URL = 'https://truthlens-api-276376440888.us-central1.run.app';
const API_KEY = process.env.REACT_APP_API_KEY;

function App() {
  const [claim, setClaim] = useState('');
  const [image, setImage] = useState(null);
  const [mode, setMode] = useState('fast');
  const [language, setLanguage] = useState('en');
  const [isVerifying, setIsVerifying] = useState(false);
  const [result, setResult] = useState(null);
  const [step, setStep] = useState('');
  const [metrics, setMetrics] = useState({ latency: 0, cost: 0 });

  useEffect(() => {
    // Register service worker
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js');
    }

    // Handle share target data
    const urlParams = new URLSearchParams(window.location.search);
    const sharedText = urlParams.get('text') || urlParams.get('title');
    if (sharedText) {
      setClaim(sharedText);
    }

    // If a shared image was provided via the service worker, fetch and attach it
    const sharedImagePath = urlParams.get('sharedImage');
    if (sharedImagePath) {
      fetch(sharedImagePath)
        .then(res => res.blob())
        .then(blob => {
          const file = new File([blob], 'shared-image', { type: blob.type || 'image/jpeg' });
          setImage(file);
        })
        .catch(() => {});
    }
  }, []);

  const handleVerification = async () => {
    if (!claim.trim()) return;

    setIsVerifying(true);
    setResult(null);
    setStep('Submitting...');
    
    const startTime = Date.now();
    
    try {
      setStep('Calling Gemini AI...');

      let response;
      if (image) {
        // Use multipart to hit unauthenticated image test endpoint
        const form = new FormData();
        form.append('text', claim);
        form.append('mode', mode);
        form.append('language', language);
        form.append('image', image);

        response = await fetch(`${API_BASE_URL}/v1/verify-image-test`, {
          method: 'POST',
          body: form
        });
      } else {
        // Text-only path uses the test endpoint (no auth required)
        const requestBody = { text: claim, mode, language };
        response = await fetch(`${API_BASE_URL}/v1/verify-test`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(requestBody)
        });
      }

      setStep('Checking Fact Database...');
      
      const data = await response.json();
      
      setStep('Generating Verdict...');
      
      const latency = Date.now() - startTime;
      setMetrics({ latency, cost: data.cost || 0 });
      
      setResult(data);
      setStep('Complete');
      
    } catch (error) {
      console.error('Verification failed:', error);
      setResult({ 
        error: 'Verification failed. Please try again.',
        verdict: 'error'
      });
    } finally {
      setIsVerifying(false);
    }
  };

  const handleImageUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      setImage(file);
    }
  };

  const getVerdictColor = (verdict) => {
    switch (verdict) {
      case 'true': return '#4caf50';
      case 'false': return '#f44336';
      case 'misleading': return '#ff9800';
      case 'unverified': return '#9e9e9e';
      default: return '#2196f3';
    }
  };

  const getVerdictIcon = (verdict) => {
    switch (verdict) {
      case 'true': return '✓';
      case 'false': return '✗';
      case 'misleading': return '⚠';
      case 'unverified': return '?';
      default: return 'ℹ';
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🔍 TruthLens</h1>
        <p>AI-Powered Fact Verification</p>
      </header>

      <main className="App-main">
        <div className="verification-form">
          <div className="input-section">
            <label htmlFor="claim">What would you like to verify?</label>
            <textarea
              id="claim"
              value={claim}
              onChange={(e) => setClaim(e.target.value)}
              placeholder="Paste text or enter a claim to verify..."
              rows={4}
            />
          </div>

          <div className="image-section">
            <label htmlFor="image">Upload image (optional)</label>
            <input
              type="file"
              id="image"
              accept="image/*"
              onChange={handleImageUpload}
            />
            {image && (
              <div className="image-preview">
                <img src={URL.createObjectURL(image)} alt="Preview" />
              </div>
            )}
          </div>

          <div className="options-section">
            <div className="option-group">
              <label htmlFor="mode">Verification Mode:</label>
              <select
                id="mode"
                value={mode}
                onChange={(e) => setMode(e.target.value)}
              >
                <option value="fast">Fast (AI only)</option>
                <option value="deep">Deep (AI + Fact Check DB)</option>
              </select>
            </div>

            <div className="option-group">
              <label htmlFor="language">Language:</label>
              <select
                id="language"
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
              >
                <option value="en">English</option>
                <option value="hi">Hindi</option>
                <option value="ta">Tamil</option>
              </select>
            </div>
          </div>

          <button
            className="verify-button"
            onClick={handleVerification}
            disabled={isVerifying || !claim.trim()}
          >
            {isVerifying ? 'Verifying...' : 'Verify Claim'}
          </button>
        </div>

        {isVerifying && (
          <div className="progress-section">
            <div className="stepper">
              <div className={`step ${step === 'Submitting...' ? 'active' : ''}`}>
                <span className="step-number">1</span>
                <span className="step-label">Submit</span>
              </div>
              <div className={`step ${step === 'Calling Gemini AI...' ? 'active' : ''}`}>
                <span className="step-number">2</span>
                <span className="step-label">Gemini</span>
              </div>
              <div className={`step ${step === 'Checking Fact Database...' ? 'active' : ''}`}>
                <span className="step-number">3</span>
                <span className="step-label">Fact DB</span>
              </div>
              <div className={`step ${step === 'Generating Verdict...' ? 'active' : ''}`}>
                <span className="step-number">4</span>
                <span className="step-label">Verdict</span>
              </div>
            </div>
            <div className="current-step">{step}</div>
          </div>
        )}

        {result && (
          <div className="result-section">
            <div className="verdict-card">
              <div 
                className="verdict-header"
                style={{ backgroundColor: getVerdictColor(result.verdict) }}
              >
                <span className="verdict-icon">
                  {getVerdictIcon(result.verdict)}
                </span>
                <span className="verdict-text">
                  {result.verdict?.toUpperCase() || 'ERROR'}
                </span>
                <span className="confidence">
                  {result.confidence ? `${Math.round(result.confidence * 100)}%` : ''}
                </span>
              </div>
              
              <div className="verdict-content">
                <h3>AI Explanation</h3>
                <p>{result.explanation || result.error}</p>
                
                {result.citations && result.citations.length > 0 && (
                  <div className="citations">
                    <h4>Verified Sources</h4>
                    <ul>
                      {result.citations.map((citation, index) => (
                        <li key={index}>
                          <a href={citation.url} target="_blank" rel="noopener noreferrer">
                            {citation.title || citation.url}
                          </a>
                          <span className="source">{citation.publisher}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>

            <div className="metrics">
              <div className="metric">
                <span className="metric-label">Latency</span>
                <span className="metric-value">{metrics.latency}ms</span>
              </div>
              <div className="metric">
                <span className="metric-label">Cost</span>
                <span className="metric-value">${metrics.cost.toFixed(4)}</span>
              </div>
            </div>
          </div>
        )}
      </main>

      <footer className="App-footer">
        <p>Powered by Google Cloud AI • Transparent • Verifiable</p>
      </footer>
    </div>
  );
}

export default App;
