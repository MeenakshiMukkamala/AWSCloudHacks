import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "./App.css";

export default function IngredientsView({ userEmail }) {
  const [ingredients, setIngredients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [updatingIds, setUpdatingIds] = useState([]); 
  const [activeUpdateItem, setActiveUpdateItem] = useState(null); 
  
  // States for consumption feature
  const [activeConsumeItem, setActiveConsumeItem] = useState(null);
  const [consumeAmount, setConsumeAmount] = useState("");
  const [isConsuming, setIsConsuming] = useState(false);
  
  const navigate = useNavigate();

  const API_URL = "https://y8hng6eo97.execute-api.us-west-2.amazonaws.com";

  // Fetch and Auto-Refresh
  useEffect(() => {
    if (!userEmail) {
      navigate("/");
      return;
    }

    const fetchDetailedIngredients = async (isSilentRefresh = false) => {
      if (!isSilentRefresh) setLoading(true);

      try {
        const normalizedEmail = userEmail.trim().toLowerCase();
        const res = await fetch(
          `${API_URL}/get-ingredients?user_id=${encodeURIComponent(normalizedEmail)}`
        );

        if (!res.ok) throw new Error("Failed to fetch");

        const text = await res.text();
        const data = JSON.parse(text);
        
        const validData = Array.isArray(data) 
          ? data.filter(item => item.ingredient_id !== "USER_META") 
          : [];
          
        setIngredients(validData);
      } catch (err) {
        console.error("Error fetching detailed ingredients:", err);
      } finally {
        if (!isSilentRefresh) setLoading(false);
      }
    };

    fetchDetailedIngredients();

    const handleVisibilityChange = () => {
      if (document.visibilityState === "visible") {
        fetchDetailedIngredients(true);
      }
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [userEmail, navigate]);

  // Update Freshness
  const handleUpdateFreshness = async (file, ingredient_id) => {
    if (!file) return;

    setUpdatingIds((prev) => [...prev, ingredient_id]);

    try {
      const base64 = await new Promise((resolve) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result.split(",")[1]);
        reader.readAsDataURL(file);
      });

      const mediaType = "." + file.type.split("/")[1];

      const res = await fetch(`${API_URL}/check-quality`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_id: userEmail,
          ingredient_id: ingredient_id,
          image: base64,
          media_type: mediaType,
        }),
      });

      if (!res.ok) throw new Error("Failed to update quality");

      const responseData = await res.json();
      const updatedIngredient = responseData.ingredient || responseData;

      setIngredients((prev) =>
        prev.map((ing) =>
          ing.ingredient_id === ingredient_id
            ? { ...ing, ...updatedIngredient }
            : ing
        )
      );
    } catch (err) {
      console.error(err);
      alert("Failed to update freshness. Please try again.");
    } finally {
      setUpdatingIds((prev) => prev.filter((id) => id !== ingredient_id));
    }
  };

  const getMaxAmount = () => {
    if (!activeConsumeItem) return null;
    
    if (activeConsumeItem.count && activeConsumeItem.count !== -1) {
      return activeConsumeItem.count;
    } else if (activeConsumeItem.weight !== undefined && activeConsumeItem.weight !== null) {
      // FORCE to string first to prevent .replace() crashes
      const weightStr = String(activeConsumeItem.weight); 
      // Renamed from 'parsed' to avoid the Babel naming collision
      const extractedNumber = parseFloat(weightStr.replace(/[^\d.]/g, ''));
      return isNaN(extractedNumber) ? null : extractedNumber;
    }
    
    return null;
  };

  const handleConsume = async (isFullRemoval = false) => {
    const numAmount = parseFloat(consumeAmount);
    
    if (!isFullRemoval && (!activeConsumeItem || isNaN(numAmount) || numAmount <= 0)) return;

    setIsConsuming(true);
    try {
      let payload;

      if (isFullRemoval) {
        payload = {
          user_id: userEmail,
          ingredient_id: activeConsumeItem.ingredient_id
        };
      } else {
        payload = {
          user_id: userEmail,
          ingredient_id: activeConsumeItem.ingredient_id,
          subtract_value: numAmount
        };
      }

      console.log("SENDING PAYLOAD TO API:", JSON.stringify(payload, null, 2));

      const res = await fetch(`${API_URL}/remove-ingredient`, { 
        method: "DELETE", // Keeping your fixed DELETE method
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const errText = await res.text();
        console.error("API Error Response:", errText); 
        throw new Error("Failed to process ingredient");
      }

      const rawText = await res.text();
      let responseData = {};
      
      if (rawText) {
        try {
          responseData = JSON.parse(rawText);
        } catch (e) {
          console.warn("Backend returned non-JSON text:", rawText);
        }
      }

      setIngredients((prev) => {
        if (responseData.status === "deleted" || isFullRemoval) {
          return prev.filter(ing => ing.ingredient_id !== activeConsumeItem.ingredient_id);
        } else {
          return prev.map((ing) => {
            if (ing.ingredient_id === activeConsumeItem.ingredient_id) {
              const updated = { ...ing };
              if (updated.count && updated.count !== -1) {
                updated.count = Math.max(0, updated.count - numAmount);
              } else if (updated.weight !== undefined && updated.weight !== null) {
                 const weightStr = String(updated.weight);
                 const currentQty = parseFloat(weightStr.replace(/[^\d.]/g, ''));
                 if (!isNaN(currentQty)) {
                   const newQty = Math.max(0, currentQty - numAmount);
                   const formattedQty = Number.isInteger(newQty) ? newQty.toString() : newQty.toFixed(2);
                   updated.weight = weightStr.replace(/[\d.]+/, formattedQty);
                 }
              }
              return updated;
            }
            return ing;
          });
        }
      });

      setActiveConsumeItem(null);
      setConsumeAmount("");
      
    } catch (err) {
      console.error("Consumption Error:", err);
      alert("Failed to update inventory. Check the console for details.");
    } finally {
      setIsConsuming(false);
    }
  };

  // CATEGORIZATION LOGIC 
  const spoiledIngredients = ingredients.filter(
    (item) => item.status === 'critical'
  );
  
  const attentionIngredients = ingredients.filter(
    (item) => item.status === 'urgent' || item.status === 'warning'
  );

  const freshIngredients = ingredients.filter(
    (item) => item.status !== 'critical' && item.status !== 'urgent' && item.status !== 'warning'
  );


  // CARD COMPONENT 
  const IngredientCard = ({ item }) => {
    let amount = "N/A";
    if (item.weight && item.weight !== "N/A") {
      amount = item.weight;
    } else if (item.count !== undefined && item.count !== null && item.count !== -1) {
      amount = `${item.count} items`;
    } else if (item.weight) {
      amount = item.weight;
    }

    const rawDate = item.date_purchased || item.date_added || item.last_updated;
    let formattedDate = "";
    if (rawDate) {
      const d = new Date(rawDate);
      if (!isNaN(d.getTime())) {
        formattedDate = d.toLocaleDateString("en-US", { 
          month: "short", day: "numeric", year: "numeric" 
        });
      } else {
        formattedDate = rawDate.split("T")[0]; 
      }
    }

    const score = item.freshness_score || 10; 
    let barColor = "#34d399"; 
    if (item.status === 'critical') {
      barColor = "#7f1d1d"; 
    } else if (item.status === 'urgent') {
      barColor = "#ef4444"; 
    } else if (item.status === 'warning') {
      barColor = "#f59e0b"; 
    }

    const isUpdating = updatingIds.includes(item.ingredient_id);

    return (
      <article 
        className="ingredient-card detailed-card" 
        key={item.ingredient_id} 
        data-ingredient-id={item.ingredient_id}
        style={{ opacity: isUpdating ? 0.6 : 1, transition: "opacity 0.2s" }} 
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px" }}>
          <div>
            <h3 style={{ fontSize: "1.4rem", margin: 0 }}>{item.name}</h3>
            {formattedDate && (
              <p style={{ margin: "2px 0 0", fontSize: "0.75rem", color: "var(--muted)" }}>
                Added: {formattedDate}
              </p>
            )}
          </div>
          <span className="metric-pill">{amount}</span>
        </div>

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: "14px" }}>
          <div className="freshness-label" style={{ margin: 0, letterSpacing: "0.05em" }}>
            <span>Freshness: {score}/10</span>
          </div>

          <div style={{ display: "flex", gap: "8px" }}>
            <button 
              className="secondary-button recheck-button" 
              onClick={() => setActiveConsumeItem(item)}
              disabled={isUpdating}
            >
            Remove
            </button>
            <button 
              className="secondary-button recheck-button" 
              onClick={() => setActiveUpdateItem(item)}
              disabled={isUpdating}
            >
              {isUpdating ? "Scanning..." : (
                <>
                  <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"></path>
                    <path d="M12 9v4"></path>
                    <path d="M12 17h.01"></path>
                  </svg>
                  Recheck
                </>
              )}
            </button>
          </div>
        </div>

        <div className="visual-bar-bg">
          <div 
            className="visual-bar-fill" 
            style={{ width: `${score * 10}%`, backgroundColor: barColor }}
          ></div>
        </div>
      </article>
    );
  };

  const maxAmount = getMaxAmount();
  const isOverLimit = maxAmount !== null && parseFloat(consumeAmount) > maxAmount;

  return (
    <main className="app-shell">
      <section className="content-grid" style={{ gridTemplateColumns: "1fr" }}>
        
        <div style={{ textAlign: "center", marginBottom: "0.5rem" }}>
          <h1>Your Ingredients</h1>
          <p className="hero-text">A detailed breakdown of your current fridge inventory.</p>
        </div>

        {loading ? (
          <div className="empty-state">Loading your inventory...</div>
        ) : (
          <>
            {/* Spoiled Section */}
            {spoiledIngredients.length > 0 && (
              <section className="card" style={{ marginBottom: "24px", border: "1px solid #fca5a5" }}>
                <p className="section-label" style={{ color: "#7f1d1d", marginBottom: "4px" }}>Time to toss</p>
                <h2>Spoiled</h2>
                <div className="ingredient-list">
                  {spoiledIngredients.map((item) => (
                    <IngredientCard key={item.ingredient_id} item={item} />
                  ))}
                </div>
              </section>
            )}

            {/* About to Spoil Section */}
            {attentionIngredients.length > 0 && (
              <section className="card accent-card" style={{ marginBottom: "24px" }}>
                <p className="section-label" style={{ color: "var(--danger-color, #ef4444)", marginBottom: "4px" }}>Needs Attention</p>
                <h2>About to Spoil</h2>
                <div className="ingredient-list">
                  {attentionIngredients.map((item) => (
                    <IngredientCard key={item.ingredient_id} item={item} />
                  ))}
                </div>
              </section>
            )}

            {/* Fresh Section */}
            {freshIngredients.length > 0 && (
              <section className="card">
                <p className="section-label" style={{ color: "var(--primary-light, #34d399)", marginBottom: "4px" }}>Fresh & Good</p>
                <h2>The Rest of the Ingredients</h2>
                <div className="ingredient-list">
                  {freshIngredients.map((item) => (
                    <IngredientCard key={item.ingredient_id} item={item} />
                  ))}
                </div>
              </section>
            )}

            {ingredients.length === 0 && (
               <p className="empty-message">Your fridge is empty! Go scan some items.</p>
            )}
          </>
        )}
      </section>

      {/* ===== RECHECK MODAL ===== */}
      {activeUpdateItem && (
        <div className="modal-overlay">
          <div className="modal-card">
            <h2>Recheck Freshness</h2>
            <p className="hero-text" style={{ marginTop: '12px', marginBottom: '32px' }}>
              Upload a new image of your <strong>{activeUpdateItem.name}</strong> to reanalyze its current quality.
            </p>

            <div className="hero-actions" style={{ justifyContent: "center", marginTop: 0 }}>
              <label className="primary-button" style={{ margin: 0 }}>
                Upload Image
                <input
                  type="file"
                  accept="image/*"
                  hidden
                  onChange={(e) => {
                    if (e.target.files[0]) {
                      handleUpdateFreshness(e.target.files[0], activeUpdateItem.ingredient_id);
                      setActiveUpdateItem(null); 
                    }
                  }}
                />
              </label>
              
              <button 
                className="secondary-button" 
                onClick={() => setActiveUpdateItem(null)}
                style={{ margin: 0 }}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ===== CONSUME/USE MODAL ===== */}
      {activeConsumeItem && (
        <div className="modal-overlay">
          <div className="modal-card">
            <h2>Use Ingredient</h2>
            <p className="hero-text" style={{ marginTop: '12px', marginBottom: '24px' }}>
              Update your inventory for <strong>{activeConsumeItem.name}</strong>.
            </p>

            <div style={{ marginBottom: "28px", textAlign: "left" }}>
              <label className="section-label" style={{ display: "flex", justifyContent: "space-between", marginBottom: "10px", color: "var(--ink)" }}>
                <span>Amount used ({activeConsumeItem.count && activeConsumeItem.count !== -1 ? 'items' : 'grams'})</span>
                {maxAmount !== null && (
                  <span style={{ color: "var(--muted)", textTransform: "none", fontWeight: "normal" }}>
                    Available: {maxAmount}
                  </span>
                )}
              </label>
              
              <input 
                type="number" 
                min="0.1"
                max={maxAmount || undefined}
                value={consumeAmount}
                onChange={(e) => setConsumeAmount(e.target.value)}
                style={{ 
                  width: "100%", 
                  padding: "14px", 
                  borderRadius: "12px", 
                  border: `1px solid ${isOverLimit ? '#ef4444' : 'var(--line)'}`,
                  background: "rgba(255, 255, 255, 0.5)",
                  fontSize: "1rem",
                  color: "var(--ink)"
                }}
                placeholder={`e.g. ${maxAmount ? Math.min(50, maxAmount) : '50'}`}
              />
              
              {/* Validation Warning */}
              {isOverLimit && (
                <p style={{ color: "#ef4444", fontSize: "0.8rem", margin: "6px 0 0" }}>
                  You cannot remove more than you have ({maxAmount}).
                </p>
              )}
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "16px", alignItems: "center" }}>
              <div className="hero-actions" style={{ justifyContent: "center", marginTop: 0, width: "100%" }}>
                <button 
                  className="primary-button" 
                  style={{ margin: 0, opacity: (!consumeAmount || isConsuming || isOverLimit) ? 0.6 : 1 }}
                  onClick={() => handleConsume(false)}
                  disabled={!consumeAmount || isConsuming || isOverLimit}
                >
                  {isConsuming && !isOverLimit ? "Updating..." : "Update Amount"}
                </button>
                
                <button 
                  className="secondary-button" 
                  onClick={() => { setActiveConsumeItem(null); setConsumeAmount(""); }}
                  style={{ margin: 0 }}
                  disabled={isConsuming}
                >
                  Cancel
                </button>
              </div>

              {/* Quick Remove Action */}
              <button 
                className="secondary-button recheck-button"
                onClick={() => {
                  if (window.confirm(`Are you sure you want to remove ${activeConsumeItem.name} entirely?`)) {
                    handleConsume(true);
                  }
                }}
                disabled={isConsuming}
                style={{ color: "#ef4444", borderColor: "rgba(239, 68, 68, 0.2)", background: "transparent" }}
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path></svg>
                Remove item entirely
              </button>
            </div>
          </div>
        </div>
      )}

    </main>
  );
}