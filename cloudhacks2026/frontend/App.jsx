import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './Login';
import Main from './main';
import './main.css';
export default function App() {
  const [userEmail, setUserEmail] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is already logged in
    const savedEmail = localStorage.getItem('userEmail');
    if (savedEmail) {
      setUserEmail(savedEmail);
    }
    setLoading(false);
  }, []);

  const handleLogin = (email) => {
    setUserEmail(email);
  };

  const handleLogout = () => {
    localStorage.removeItem('userEmail');
    setUserEmail(null);
  };

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        backgroundColor: '#f5f5f5'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div className="loader"></div>
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <Router>
      <Routes>
        <Route
          path="/login"
          element={userEmail ? <Navigate to="/" /> : <Login onLogin={handleLogin} />}
        />
        <Route
          path="/"
          element={userEmail ? <Main userEmail={userEmail} onLogout={handleLogout} /> : <Navigate to="/login" />}
        />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </Router>
  );
}
