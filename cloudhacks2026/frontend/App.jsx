import { useState, useEffect } from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
  useNavigate,
} from "react-router-dom";

import Login from "./Login";
import Main from "./main";
import "./App.css";

function Landing({ ingredients, setIngredients }) 
{
  const navigate = useNavigate();

  return (
    <main className="app-shell">
      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">Scrapless kitchen planner</p>
          <h1>Cook what you already have before it goes bad.</h1>
          <p className="hero-text">
            Keep an eye on ingredients, spot what needs attention, and turn
            fridge leftovers into easy meals.
          </p>

          <div className="hero-actions">
            <button
              className="primary-button"
              onClick={() => navigate("/login")}
            >
              Scan my ingredients
            </button>

            <button className="secondary-button">
              View sample plan
            </button>
          </div>
        </div>
      </section>  

      <section className="content-grid">
        <section className="card">
          <div className="section-heading">
            <div>
              <p className="section-label">Fridge watchlist</p>
              <h2>Ingredients needing attention</h2>
            </div>
          </div>

          {ingredients.length > 0 ? (
            <div className="ingredient-list">
              {ingredients
                .sort((a, b) => {
                  // Sort by days_remaining in ascending order (least fresh first)
                  if (a.days_remaining === null) return 1;
                  if (b.days_remaining === null) return -1;
                  return a.days_remaining - b.days_remaining;
                })
                .map((item, idx) => (
                <article className="ingredient-card" key={idx}>
                  <div className="ingredient-top">
                    <div>
                      <h3>{item.name}</h3>
                      <p>{item.freshness_status || "Unknown freshness"}</p>
                    </div>
                    <strong>{item.days_remaining !== null ? `${item.days_remaining}d left` : "Freshness unknown"}</strong>
                  </div>

                  {item.quantity && (
                    <p className="recipe-line">
                      Quantity: <span>{item.quantity}</span>
                    </p>
                  )}

                  {item.freshness_notes && (
                    <p className="recipe-line">
                      Details: <span>{item.freshness_notes}</span>
                    </p>
                  )}

                  {item.expiration_date && (
                    <p className="recipe-line">
                      Expires: <span>{item.expiration_date}</span>
                    </p>
                  )}

                  {item.category && (
                    <p className="recipe-line">
                      Category: <span>{item.category}</span>
                    </p>
                  )}
                </article>
              ))}
            </div>
          ) : (
            <div className="ingredient-list empty-state">
              <p className="empty-message">Upload or take a photo to see your ingredients here</p>
            </div>
          )}
        </section>

        <section className="card accent-card">
          <p className="section-label">Tonight's idea</p>
          <h2>Your meal suggestions</h2>

          <p className="accent-copy">
            Once you upload a photo of your ingredients, we'll suggest recipes using items that need attention.
          </p>

          <div className="steps empty-state">
            <p className="empty-message">Sign in and upload ingredients to get personalized meal suggestions</p>
          </div>
        </section>
      </section>
    </main>
  );
}

export default function App() {
  const [userEmail, setUserEmail] = useState(null);
  const [ingredients, setIngredients] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const savedEmail = localStorage.getItem("userEmail");
    if (savedEmail) setUserEmail(savedEmail);
    setLoading(false);
  }, []);

  const handleLogin = (email) => {
    localStorage.setItem("userEmail", email);
    setUserEmail(email);
  };

  const handleLogout = () => {
    localStorage.removeItem("userEmail");
    setUserEmail(null);
    setIngredients([]);
  };

  if (loading) return <div className="loader">Loading...</div>;

  return (
    <Router>
      <Routes>
        {/* Landing */}
        <Route path="/" element={<Landing ingredients={ingredients} setIngredients={setIngredients} />} />

        {/* Login */}
        <Route
          path="/login"
          element={
            userEmail
              ? <Navigate to="/app" />
              : <Login onLogin={handleLogin} />
          }
        />

        {/* Main app */}
        <Route
          path="/app"
          element={
            userEmail
              ? <Main userEmail={userEmail} onLogout={handleLogout} setAppIngredients={setIngredients} />
              : <Navigate to="/login" />
          }
        />

        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </Router>
  );
}