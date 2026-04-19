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

const API_URL = "https://y8hng6eo97.execute-api.us-west-2.amazonaws.com";

function Landing({ ingredients }) {
  const navigate = useNavigate();

  const [meal, setMeal] = useState(null);
  const [mealLoading, setMealLoading] = useState(false);

  // 🔥 Fetch meal using meal_planner Lambda
  useEffect(() => {
  const fetchMeal = async () => {
    const email = localStorage.getItem("userEmail");
    if (!email) return;

    setMealLoading(true);

    try {
      const res = await fetch(
        `${API_URL}/get-meal?user_id=${encodeURIComponent(email)}&action=suggest&meal_type=any`
      );

      const data = await res.json();
      console.log("MEAL RESPONSE:", data);

      if (data.meal) {
        setMeal(data.meal);
      }
    } catch (err) {
      console.error("Meal fetch error:", err);
    } finally {
      setMealLoading(false);
    }
  };

  fetchMeal();
}, [ingredients]);  

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
              onClick={() => navigate("/app")}
            >
              Scan my ingredients
            </button>

            <button className="secondary-button">
              View sample plan
            </button>
          </div>
        </div>
      </section>

      {/* INGREDIENTS */}
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
              {[...ingredients]
                .sort((a, b) => {
                  const aDays = a.days_remaining ?? null;
                  const bDays = b.days_remaining ?? null;

                  if (aDays === null && bDays !== null) return -1;
                  if (bDays === null && aDays !== null) return 1;
                  if (aDays === null && bDays === null) return 0;

                  return Number(aDays) - Number(bDays);
                })
                .map((item, idx) => {
                  const status =
                    item.freshness_status ||
                    item.status ||
                    item.freshness_notes ||
                    "Unknown freshness";

                  const expiration =
                    item.expiration_date ||
                    item.estimated_expiration ||
                    null;

                  const quantity =
                    item.quantity ||
                    (item.count && item.count !== -1
                      ? `${item.count} items`
                      : item.weight
                      ? `${item.weight}`
                      : null);

                  return (
                    <article
                      className="ingredient-card"
                      key={item.ingredient_id || idx}
                    >
                      <div className="ingredient-top">
                        <div>
                          <h3>{item.name || "Unnamed item"}</h3>
                          <p>{status}</p>
                        </div>

                        <strong>
                          {item.days_remaining != null
                            ? `${item.days_remaining}d left`
                            : expiration
                            ? `Expires ${expiration}`
                            : "Freshness unknown"}
                        </strong>
                      </div>

                      {quantity && (
                        <p className="recipe-line">
                          Quantity: <span>{quantity}</span>
                        </p>
                      )}

                      {item.freshness_notes && (
                        <p className="recipe-line">
                          Details: <span>{item.freshness_notes}</span>
                        </p>
                      )}

                      {expiration && (
                        <p className="recipe-line">
                          Expires: <span>{expiration}</span>
                        </p>
                      )}
                    </article>
                  );
                })}
            </div>
          ) : (
            <div className="ingredient-list empty-state">
              <p className="empty-message">
                Upload or take a photo to see your ingredients here
              </p>
            </div>
          )}
        </section>
      </section>

      {/* 🍽 MEAL PLAN */}
      <section className="card accent-card">
        <p className="section-label">Tonight's dinner</p>
        <h2>Your meal suggestion</h2>

        {mealLoading ? (
  <div className="steps">
    <p className="empty-message">
      Finding the best meal for your ingredients...
    </p>
  </div>
) : meal ? (
  <div className="meal-card">
    <h3>{meal.name}</h3>

    {meal.description && (
      <p className="accent-copy">{meal.description}</p>
    )}

    {meal.ingredients_used && (
      <p className="recipe-line">
        Uses:{" "}
        <span>
          {meal.ingredients_used.map((i) => i.name).join(", ")}
        </span>
      </p>
    )}

    {meal.steps && (
      <div className="recipe-steps">
        <p className="recipe-line"><strong>Recipe:</strong></p>
        <ol>
          {meal.steps.map((step, idx) => (
            <li key={idx}>{step}</li>
          ))}
        </ol>
      </div>
    )}
  </div>
) : (
  <div className="steps empty-state">
    <p className="empty-message">
      Add ingredients to get a personalized meal recommendation
    </p>
  </div>
)}  </section>
    </main>
  );
}

export default function App() {
  const [userEmail, setUserEmail] = useState(null);
  const [ingredients, setIngredients] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const savedEmail = localStorage.getItem("userEmail");

    if (savedEmail) {
      const normalized = savedEmail.trim().toLowerCase();
      setUserEmail(normalized);
    }

    setLoading(false);
  }, []);

  const handleLogin = (email) => {
    const normalized = email.trim().toLowerCase();
    localStorage.setItem("userEmail", normalized);
    setUserEmail(normalized);
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
        <Route
          path="/"
          element={
            userEmail ? (
              <Landing ingredients={ingredients} />
            ) : (
              <Login onLogin={handleLogin} />
            )
          }
        />

        <Route
          path="/app"
          element={
            userEmail ? (
              <Main
                userEmail={userEmail}
                onLogout={handleLogout}
                setAppIngredients={setIngredients}
              />
            ) : (
              <Navigate to="/" />
            )
          }
        />

        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </Router>
  );
}