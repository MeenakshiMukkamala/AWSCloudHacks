import { useState } from "react";
import { useNavigate } from "react-router-dom";
import apiClient from "./api";
import "./main.css";

export default function Main({ userEmail, setAppIngredients }) {
  
  const [uploadedImage, setUploadedImage] = useState(null);
  const [ingredients, setIngredients] = useState([]);
  const [loading, setLoading] = useState(false);

  const navigate = useNavigate(); // ✅ for going back

      // await fetchIngredients();
      // setLoading(false);
      // navigate("/");

  const API_URL = import.meta.env.VITE_API_URL;
  


const normalizedEmail = userEmail?.trim().toLowerCase();
const fetchIngredients = async () => {
  setLoading(true);
  try {
    const res = await fetch(
      `https://y8hng6eo97.execute-api.us-west-2.amazonaws.com/get-ingredients?user_id=${encodeURIComponent(normalizedEmail)}`
    );

    const text = await res.text();
    console.log("STATUS:", res.status);
    console.log("RAW RESPONSE:", text);

    if (!res.ok) {
      throw new Error(`Server error ${res.status}`);
    }

    let data = [];
    try {
      data = JSON.parse(text);
    } catch {
      console.warn("Response not JSON");
    }

    setAppIngredients(data || []);
    navigate("/");
  } catch (err) {
    console.error("Fetch error:", err);
    alert("Something went wrong fetching ingredients");
  } finally {
    setLoading(false);
  }
};

const saveIngredients = async () => {
  setLoading(true);
  try {
    await apiClient.saveIngredients(normalizedEmail, ingredients);
    await fetchIngredients(); // refresh + navigate
  } catch (err) {
    console.error("Error saving ingredients:", err);
    alert("Failed to save ingredients. Please try again.");
  } finally {
    setLoading(false); // always reset loading
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
    
    // Extract ingredients from response and set state
    if (data.ingredients) {
      setIngredients(data.ingredients);
    }

  } catch (err) {
    console.error(err);
    alert("Failed to analyze image. Please try again.");
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
          <p className="eyebrow">Your Kitchen</p>
          <h1>Scan Ingredients</h1>
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
                      Expires:{" "}
                      <span>
                        {new Date(item.expiration_date).toLocaleDateString("en-US", {
                          year: "numeric",
                          month: "2-digit",
                          day: "2-digit",
                        })}
                      </span>
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
                onClick={saveIngredients}
                disabled={loading}
              >
                {loading ? "Saving..." : "Save"}
              </button>
            </div>
          </section>
        </section>
      )}
    </main>
  );
}