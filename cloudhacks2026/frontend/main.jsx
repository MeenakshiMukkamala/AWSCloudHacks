import React, { useState } from 'react';
import './main.css';

export default function Scrapless() {
  const [uploadedImage, setUploadedImage] = useState(null);
  const [ingredients, setIngredients] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedIngredient, setSelectedIngredient] = useState(null);

  const handleImageUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      setUploadedImage(event.target.result);
    };
    reader.readAsDataURL(file);

    // Send to backend for AI analysis
    await analyzeImage(file);
  };

  const handleCameraCapture = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      setUploadedImage(event.target.result);
    };
    reader.readAsDataURL(file);

    await analyzeImage(file);
  };

  const analyzeImage = async (file) => {
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('image', file);

      const response = await fetch('/api/analyze-ingredients', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        setIngredients(data.ingredients || []);
      }
    } catch (error) {
      console.error('Error analyzing image:', error);
    } finally {
      setLoading(false);
    }
  };


  const getFreshnessColor = (daysLeft) => {
    if (daysLeft > 5) return '#10b981'; // Green
    if (daysLeft > 1) return '#f59e0b'; // Amber
    return '#ef4444'; // Red
  };

  const getFreshnessLabel = (daysLeft) => {
    if (daysLeft > 5) return 'Fresh';
    if (daysLeft > 2) return 'Use Soon';
    return 'Use Today';
  };

  const getCardBackgroundColor = (daysLeft) => {
    if (daysLeft > 5) return '#dcfce7'; // Light green for "Good shape"
    if (daysLeft > 2) return '#fef3c7'; // Light yellow for "Use Soon"
    return '#fee2e2'; // Light red for "Use Today"
  };

  return (
    <div className="scrapless-container">
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <h1 className="logo">Scrapless</h1>
          <p className="tagline">Reduce food waste, maximize freshness</p>
        </div>
      </header>

      {/* Main Content */}
      <main className="main-content">
        {/* Upload Section */}
        <section className="upload-section">
          <div className="upload-container">
            <h2>Snap a photo of your ingredients</h2>
            <p className="upload-description">
              Upload an image or take a photo of your fridge contents. Our AI will identify what you have and track freshness.
            </p>

            <div className="upload-buttons">
              <label className="upload-button camera-button">
                <span>Take Photo</span>
                <input
                  type="file"
                  accept="image/*"
                  capture="environment"
                  onChange={handleCameraCapture}
                  style={{ display: 'none' }}
                />
              </label>

              <label className="upload-button upload-file-button">
                <span>Upload Image</span>
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleImageUpload}
                  style={{ display: 'none' }}
                />
              </label>
            </div>
          </div>

          {/* Image Preview */}
          {uploadedImage && (
            <div className="image-preview-container">
              <img src={uploadedImage} alt="Uploaded" className="image-preview" />
            </div>
          )}
        </section>

        {/* Loading State */}
        {loading && (
          <section className="loading-section">
            <div className="loader"></div>
            <p>Analyzing your ingredients...</p>
          </section>
        )}

        {/* Ingredients Section */}
        {ingredients.length > 0 && !loading && (
          <section className="ingredients-section">
            <h2>Your Ingredients</h2>
            <p className="section-description">
              {ingredients.length} item{ingredients.length !== 1 ? 's' : ''} identified
            </p>

            <div className="ingredients-grid">
              {ingredients.map((ingredient, index) => (
                <div
                  key={index}
                  className="ingredient-card"
                  onClick={() => setSelectedIngredient(selectedIngredient === index ? null : index)}
                  style={{ 
                    cursor: 'pointer',
                    backgroundColor: getCardBackgroundColor(ingredient.daysLeft)
                  }}
                >
                  <h3 className="ingredient-name">{ingredient.name}</h3>

                  <div className="freshness-container">
                    <div
                      className="freshness-bar"
                      style={{
                        backgroundColor: getFreshnessColor(ingredient.daysLeft),
                        width: `${(ingredient.daysLeft / 10) * 100}%`,
                      }}
                    ></div>
                  </div>

                  <div className="freshness-info">
                    <span
                      className="freshness-badge"
                      style={{
                        backgroundColor: getFreshnessColor(ingredient.daysLeft),
                        color: 'white',
                      }}
                    >
                      {getFreshnessLabel(ingredient.daysLeft)}
                    </span>
                    <span className="days-left">{ingredient.daysLeft} days</span>
                  </div>

                  {/* Expanded Details */}
                  {selectedIngredient === index && (
                    <div className="ingredient-details">
                      <div className="storage-tip">
                        <strong>Storage Tip:</strong>
                        <p>{ingredient.storageTip}</p>
                      </div>
                      <div className="usage-suggestions">
                        <strong>Use in:</strong>
                        <div className="suggestions-list">
                          {ingredient.recipes && ingredient.recipes.map((recipe, idx) => (
                            <span key={idx} className="suggestion-tag">
                              {recipe}
                            </span>
                          ))}
                        </div>
                      </div>
                      <div className="condition">
                        <strong>Condition:</strong>
                        <p>{ingredient.condition}</p>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Empty State */}
        {!uploadedImage && ingredients.length === 0 && !loading && (
          <section className="empty-state">
            <h3>Ready to reduce food waste?</h3>
            <p>Upload a photo of your fridge to get started</p>
          </section>
        )}
      </main>

      {/* Footer */}
      <footer className="footer">
        <p>Scrapless © 2024 - Making a difference, one ingredient at a time</p>
      </footer>
    </div>
  );
}
