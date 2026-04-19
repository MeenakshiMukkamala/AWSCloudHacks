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
import IngredientsView from "./IngredientsView";
import "./App.css";

const API_URL = "https://y8hng6eo97.execute-api.us-west-2.amazonaws.com";

function Landing({ ingredients, setIngredients, onLogout }) {  
  const navigate = useNavigate();
  const [meal, setMeal] = useState(null);
  const [mealLoading, setMealLoading] = useState(false);

  const handleUseMeal = async () => {
    if (!meal || !meal.ingredients_used) {
      console.warn("No meal or ingredients_used");
      return;
    }

    const email = localStorage.getItem("userEmail");

    try {
      const res = await fetch(`${API_URL}/get-meal`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_id: email,
          action: "accept",
          ingredients_used: meal.ingredients_used,
        }),
      });

      const text = await res.text();
      console.log("USE MEAL RAW:", text);

      let data = {};
      try {
        data = JSON.parse(text);
      } catch {
        console.error("Bad JSON:", text);
      }

      // 🔥 clear meal immediately
      setMeal(null);

      // 🔥 refetch ingredients
      const ingRes = await fetch(
        `${API_URL}/get-ingredients?user_id=${encodeURIComponent(email)}`
      );

      const ingText = await ingRes.text();
      console.log("REFETCH ING:", ingText);

      let ingData = [];
      try {
        ingData = JSON.parse(ingText);
      } catch {}

      if (Array.isArray(ingData)) {
        setIngredients(ingData);
      }

    } catch (err) {
      console.error("Use meal error:", err);
    }
  };

  useEffect(() => {
    const fetchMeal = async () => {
      const email = localStorage.getItem("userEmail");
      if (!email) return;

      setMealLoading(true);

      try {
        const res = await fetch(
          `${API_URL}/get-meal?user_id=${encodeURIComponent(
            email
          )}&action=suggest&meal_type=any`
        );

        const text = await res.text(); // 🔥 get raw response
        console.log("RAW MEAL RESPONSE:", text);

        let data;
        try {
          data = JSON.parse(text);
        } catch (e) {
          console.error("Not JSON:", text);
          setMeal(null);
          return;
        }

        // 🔥 handle all cases
        if (data.meal) {
          setMeal(data.meal);
        } else {
          console.warn("No meal returned:", data);
          setMeal(null);
        }

      } catch (err) {
        console.error("Meal fetch error:", err);
        setMeal(null);
      } finally {
        setMealLoading(false);
      }
    };

    fetchMeal();
  }, []);

  return (
    <main className="app-shell">
      <nav className="app-nav">
        <div className="nav-logo-section">
          <img className="nav-logo-img" src="/favicon.png" alt="Scrapless Logo"/>
          <h1 className="nav-logo-text">Scrapless</h1>
        </div>
        <button className="secondary-button" onClick={onLogout}> Sign Out </button>
      </nav>

      {/* NEW OVERARCHING GRID CONTAINER */}
      <div className="main-content-grid">

        {/* LEFT COLUMN: Hero + Watchlist */}
        <div className="left-stack">
          
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
                  Scan My Ingredients
                </button>

                <button
                  className="secondary-button" 
                  onClick={() => navigate("/inventory")}
                >
                  View My Ingredients
                </button>
              </div>
            </div>
          </section>

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
                  .filter(item =>
                    item.name &&
                    item.name.trim() !== "" &&
                    item.ingredient_id !== "USER_META"
                  )
                  .sort((a, b) => {
                    const aDays = a.days_remaining ?? null;
                    const bDays = b.days_remaining ?? null;

                    if (aDays === null && bDays !== null) return -1;
                    if (bDays === null && aDays !== null) return 1;
                    if (aDays === null && bDays === null) return 0;

                    return Number(aDays) - Number(bDays);
                  })
                  .slice(0, 4)
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

        </div>

        {/* RIGHT COLUMN: Meal Suggestion */}
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

              {/* 🔥 CLEAN INGREDIENT LIST */}
              {meal.ingredients_used && (
                <div className="recipe-section">
                  <p className="recipe-title">Ingredients</p>
                  <ul className="ingredient-tags">
                    {[...new Set(meal.ingredients_used.map(i => i.name))]
                      .map((name, idx) => (
                        <li key={idx}>{name}</li>
                      ))}
                  </ul>
                </div>
              )}

              {/* 🔥 RECIPE STEPS */}
              {meal.steps && (
                <div className="recipe-section">
                  <p className="recipe-title">Steps</p>
                  <ol className="recipe-steps">
                    {meal.steps.map((step, idx) => (
                      <li key={idx}>{step}</li>
                    ))}
                  </ol>
                </div>
              )}

              <button
                className="primary-button"
                onClick={handleUseMeal}
                style={{ marginTop: "12px" }}
              >
                Use this meal
              </button>
            </div>
          ) : (
            <div className="steps empty-state">
              <p className="empty-message">
                Add ingredients to get a personalized meal recommendation
              </p>
            </div>
          )}
        </section>

      </div>
    </main>
  );
}

export default function App() {
  const [userEmail, setUserEmail] = useState(null);
  const [ingredients, setIngredients] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
  const sessionEmail = sessionStorage.getItem("userEmail");

  if (sessionEmail) {
    setUserEmail(sessionEmail);
  }

  setLoading(false);
}, []);
  
  useEffect(() => {
    const fetchIngredients = async () => {
      if (!userEmail) return;

      try {
        const res = await fetch(
          `${API_URL}/get-ingredients?user_id=${encodeURIComponent(userEmail)}`
        );

        const text = await res.text();
        console.log("INGREDIENT RAW:", text);

        let data = [];
        try {
          data = JSON.parse(text);
        } catch (e) {
          console.error("Invalid JSON:", text);
        }

        if (Array.isArray(data)) {
          setIngredients(data);
        }
      } catch (err) {
        console.error("Ingredient fetch error:", err);
      }
    };

    fetchIngredients();
  }, [userEmail]);
  const handleLogin = (email) => {
  const normalized = email.trim().toLowerCase();

      // use sessionStorage instead
      sessionStorage.setItem("userEmail", normalized);
      setUserEmail(normalized);
    };
    const handleLogout = () => {
      sessionStorage.removeItem("userEmail");
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
                <Landing
                  ingredients={ingredients}
                  setIngredients={setIngredients}
                  onLogout={handleLogout}
                />
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

        <Route
          path="/inventory"
          element={
            userEmail ? (
              <IngredientsView userEmail={userEmail} />
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