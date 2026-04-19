import { useState } from "react";
import { useNavigate } from "react-router-dom";
import "./main.css";

export default function Main({ userEmail, onLogout, setAppIngredients }) {
  
  const [uploadedImage, setUploadedImage] = useState(null);
  const [ingredients, setIngredients] = useState([]);
  const [loading, setLoading] = useState(false);

  const navigate = useNavigate(); // ✅ for going back

  const API_URL = import.meta.env.VITE_API_URL;

  const fetchIngredients = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/get-ingredients`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_id: userEmail,
        }),
      });

      const data = await res.json();
      setAppIngredients(data || []);
      navigate("/");
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleFile = async (file) => {
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const fullDataURL = event.target.result;
      setUploadedImage(fullDataURL);
    };
    
    reader.readAsDataURL(file);

    await analyzeImage(file);
 
  };

  const analyzeImage = async (file) => {
  setLoading(true);

  try {
    const base64 = await new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result.split(",")[1]);
      reader.readAsDataURL(file);
    });

    const res = await fetch('https://y8hng6eo97.execute-api.us-west-2.amazonaws.com/add-ingredients', {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        user_id: userEmail,
        image: base64,
        media_type: "." + file.type.split("/")[1]
      }),
    });

    const data = await res.json();    

    // OPTIONAL: small delay so user sees "analyzing"
    setTimeout(() => {
      // RESET UI BACK TO MAIN PAGE
      setUploadedImage(null);
      setIngredients([]);
    }, 800);

  } catch (err) {
    console.error(err);
  } finally {
    setLoading(false);
  }
};

  return (
    <main className="app-shell">
      {/* HERO (centered) */}
      <section
        className="hero"
        style={{ display: "flex", justifyContent: "center" }}
      >
        <div
          className="hero-copy"
          style={{
            maxWidth: "600px",
            width: "100%",
            textAlign: "center",
          }}
        >
          <p className="eyebrow">Your kitchen</p>
          <h1>Scan your ingredients</h1>
          <p className="hero-text">
            Upload a photo to track freshness and get meal ideas.
            (Please upload images that are '.jpg', '.jpeg', '.png', '.webp', '.gif' and less than 10MB only.)
          </p>

          <div
            className="hero-actions"
            style={{ justifyContent: "center" }}
          >
              <label className="primary-button">
                Upload Image
                <input
                  type="file"
                  accept="image/*"
                  hidden
                  onChange={(e) => handleFile(e.target.files[0])}
                />
              </label>

              <button className="primary-button" onClick={fetchIngredients}>
                View My Ingredients
              </button>

              <button className="secondary-button" onClick={onLogout}>
                Sign Out
              </button>
            </div>
          </div>
        </section>

      {/* IMAGE PREVIEW */}
      {uploadedImage && (
        <section
          className="content-grid"
          style={{ display: "flex", justifyContent: "center" }}
        >
          <section
            className="card"
            style={{ width: "700px", maxWidth: "100%" }}
          >
            <p className="section-label">Uploaded Image</p>
            <img
              src={uploadedImage}
              alt="preview"
              style={{
                width: "100%",
                borderRadius: "20px",
                marginTop: "12px",
              }}
            />
          </section>
        </section>
      )}

      {/* LOADING */}
      {loading && (
        <section
          className="content-grid"
          style={{ display: "flex", justifyContent: "center" }}
        >
          <section
            className="card"
            style={{ width: "700px", maxWidth: "100%" }}
          >
            <p>Analyzing your ingredients...</p>
          </section>
        </section>
      )}

      {/* RESULTS */}
      {ingredients.length > 0 && !loading && (
        <section
          className="content-grid"
          style={{ display: "flex", justifyContent: "center" }}
        >
          <section
            className="card"
            style={{ width: "700px", maxWidth: "100%" }}
          >
            <div className="section-heading">
              <div>
                <p className="section-label">Detected items</p>
                <h2>Your Ingredients</h2>
              </div>
            </div>

            <div className="ingredient-list">
              {ingredients.map((item, idx) => (
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

            {/* ✅ SAVE BUTTON */}
            <div style={{ marginTop: "24px", textAlign: "center" }}>
              <button
                className="primary-button"
                onClick={() => {
                  setIngredients([]);
                  setUploadedImage(null);
                }}
              >
                Clear and Upload More
              </button>
            </div>
          </section>
        </section>
      )}
    </main>
  );
}