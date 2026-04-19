import React, { useState } from 'react';
import './login.css';

const API_URL = "https://y8hng6eo97.execute-api.us-west-2.amazonaws.com";

export default function Login({ onLogin }) {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const validateEmail = () => {
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError('Please enter a valid email address');
      return false;
    }
    return true;
  };

  // 🔐 SIGN IN
  const handleSignIn = async (e) => {
  e.preventDefault();
  setError('');

  if (!validateEmail()) return;

  setLoading(true);
  try {
    const res = await fetch(
      `${API_URL}/get-user?user_id=${encodeURIComponent(email)}`
    );

    if (res.status === 404) {
      setError("No account found. Please sign up.");
      return;
    }

    if (!res.ok) {
      throw new Error("Server error");
    }

    // user exists → log in
    localStorage.setItem('userEmail', email);
    onLogin(email);

  } catch (err) {
    console.error(err);
    setError("Failed to sign in.");
  } finally {
    setLoading(false);
  }
};
  // 🆕 SIGN UP → calls API Gateway
  const handleSignUp = async () => {
  setError('');

  if (!validateEmail()) return;

  setLoading(true);
  try {
    const res = await fetch(`${API_URL}/add-user`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        user_id: email,
      }),
    });

    const text = await res.text();

    // 🔥 handle "user already exists"
    if (res.status === 409) {
      setError("Account already exists. Please sign in.");
      return;
    }

    if (!res.ok) {
      throw new Error(text);
    }

    // success → log in
    localStorage.setItem('userEmail', email);
    onLogin(email);

  } catch (err) {
    console.error(err);
    setError("Failed to sign up. Try again.");
  } finally {
    setLoading(false);
  }
};

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <img className="login-img" src="/favicon.png" alt="Scrapless Logo"/>
          <h1 className="login-logo">Scrapless</h1>
          <p className="login-tagline">Reduce food waste, maximize freshness</p>
        </div>

        <form onSubmit={handleSignIn} className="login-form">
          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email"
              disabled={loading}
              autoFocus
            />
          </div>

          {error && <div className="error-message">{error}</div>}

          {/* 🔥 Buttons */}
          <div className="button-row">
            <button
              type="submit"
              className="auth-button primary"
              disabled={loading}
            >
              {loading ? "..." : "Sign In"}
            </button>

            <button
              type="button"
              className="auth-button secondary"
              onClick={handleSignUp}
              disabled={loading}
            >
              {loading ? "..." : "Sign Up"}
            </button>
          </div>
        </form>

        <div className="login-footer">
          <p>Your account gives you access to track your ingredients across devices</p>
        </div>
      </div>
    </div>
  );
}