/**
 * EXAMPLE COMPONENT - Advanced Usage
 * 
 * This file demonstrates how to use all the utility functions and hooks
 * available in the Scrapless frontend. This is for reference and learning purposes.
 * 
 * Uncomment and adapt this code to use in your components.
 */

import React, { useState } from 'react';
import { useImageAnalysis, useRecipeSuggestions, useLocalStorage } from './hooks';
import apiClient from './api';
import {
  getFreshnessColor,
  getFreshnessLabel,
  sortIngredientsByFreshness,
  filterIngredientsNearExpiry,
  filterFreshIngredients,
  validateImage,
} from './utils';

/**
 * Example: Advanced Ingredient Manager Component
 * Shows how to use all available utilities and hooks
 */
export function AdvancedIngredientManager() {
  // Use custom hook for image analysis
  const {
    loading,
    error,
    ingredients,
    uploadedImage,
    analyzeImage,
    clearData,
  } = useImageAnalysis();

  // Use custom hook for recipe suggestions
  const { recipes, fetchRecipes } = useRecipeSuggestions();

  // Use local storage to persist ingredients
  const [savedIngredients, setSavedIngredients] = useLocalStorage(
    'scrapless_ingredients',
    []
  );

  // Local state
  const [sortBy, setSortBy] = useState('freshness'); // 'freshness' or 'name'
  const [filterType, setFilterType] = useState('all'); // 'all', 'urgent', 'fresh'

  /**
   * Handle image upload with validation
   */
  const handleImageUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Validate image
    const validation = validateImage(file);
    if (!validation.valid) {
      alert(validation.error);
      return;
    }

    // Analyze image
    await analyzeImage(file);
  };

  /**
   * Get processed ingredients based on sorting and filtering
   */
  const getProcessedIngredients = () => {
    let processed = ingredients;

    // Filter
    if (filterType === 'urgent') {
      processed = filterIngredientsNearExpiry(processed, 2);
    } else if (filterType === 'fresh') {
      processed = filterFreshIngredients(processed, 5);
    }

    // Sort
    if (sortBy === 'freshness') {
      processed = sortIngredientsByFreshness(processed);
    } else if (sortBy === 'name') {
      processed = [...processed].sort((a, b) =>
        a.name.localeCompare(b.name)
      );
    }

    return processed;
  };

  /**
   * Save ingredient to local storage
   */
  const saveIngredient = (ingredient) => {
    const updated = [...savedIngredients];
    const index = updated.findIndex((i) => i.name === ingredient.name);

    if (index > -1) {
      updated[index] = ingredient;
    } else {
      updated.push(ingredient);
    }

    setSavedIngredients(updated);
  };

  /**
   * Get recipe suggestions for current ingredients
   */
  const handleGetRecipes = async () => {
    const ingredientNames = ingredients.map((i) => i.name);
    try {
      await fetchRecipes(ingredientNames);
    } catch (error) {
      console.error('Failed to fetch recipes:', error);
    }
  };

  /**
   * Get storage tips for an ingredient
   */
  const getStorageTips = async (ingredientName) => {
    try {
      const tips = await apiClient.getStorageTips(ingredientName);
      return tips;
    } catch (error) {
      console.error('Failed to get storage tips:', error);
      return null;
    }
  };

  const processedIngredients = getProcessedIngredients();

  return (
    <div className="advanced-manager">
      {/* Upload Section */}
      <div className="upload-area">
        <h2>Upload Ingredients Photo</h2>
        <input
          type="file"
          accept="image/*"
          onChange={handleImageUpload}
          disabled={loading}
        />
        {loading && <p>Analyzing...</p>}
        {error && <p style={{ color: 'red' }}>{error}</p>}
      </div>

      {/* Image Preview */}
      {uploadedImage && (
        <div className="preview">
          <img src={uploadedImage} alt="Uploaded" style={{ maxWidth: '300px' }} />
        </div>
      )}

      {/* Controls */}
      <div className="controls">
        <div>
          <label>
            Sort by:
            <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
              <option value="freshness">Freshness (expires first)</option>
              <option value="name">Name (A-Z)</option>
            </select>
          </label>
        </div>

        <div>
          <label>
            Filter:
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
            >
              <option value="all">All ingredients</option>
              <option value="urgent">Urgent (use today)</option>
              <option value="fresh">Fresh (good for days)</option>
            </select>
          </label>
        </div>

        <button onClick={handleGetRecipes} disabled={ingredients.length === 0}>
          Get Recipes
        </button>

        <button onClick={clearData}>Clear</button>
      </div>

      {/* Ingredients Grid */}
      <div className="ingredients-display">
        <h3>
          Ingredients ({processedIngredients.length} of {ingredients.length})
        </h3>

        {processedIngredients.length === 0 ? (
          <p>No ingredients to display</p>
        ) : (
          <div className="grid">
            {processedIngredients.map((ingredient, idx) => (
              <div
                key={idx}
                className="ingredient-item"
                style={{
                  borderLeftColor: getFreshnessColor(ingredient.daysLeft),
                }}
              >
                <h4>{ingredient.name}</h4>
                <p>Days left: {ingredient.daysLeft}</p>
                <span
                  style={{
                    backgroundColor: getFreshnessColor(ingredient.daysLeft),
                    color: 'white',
                    padding: '4px 8px',
                    borderRadius: '4px',
                    fontSize: '12px',
                  }}
                >
                  {getFreshnessLabel(ingredient.daysLeft)}
                </span>

                <p>{ingredient.condition}</p>

                <button
                  onClick={() => saveIngredient(ingredient)}
                  style={{ marginTop: '8px', marginRight: '8px' }}
                >
                  Save
                </button>

                <button
                  onClick={() => getStorageTips(ingredient.name)}
                  style={{ marginTop: '8px' }}
                >
                  Storage Tips
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Recipe Suggestions */}
      {recipes.length > 0 && (
        <div className="recipes-section">
          <h3>Recipe Suggestions</h3>
          <div className="recipes-grid">
            {recipes.map((recipe, idx) => (
              <div key={idx} className="recipe-card">
                <h4>{recipe.name}</h4>
                <p>{recipe.description}</p>
                <p>
                  <strong>Ingredients needed:</strong>{' '}
                  {recipe.ingredientsNeeded?.join(', ')}
                </p>
                {recipe.url && (
                  <a href={recipe.url} target="_blank" rel="noopener noreferrer">
                    View Recipe
                  </a>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Saved Ingredients */}
      {savedIngredients.length > 0 && (
        <div className="saved-section">
          <h3>Saved Ingredients</h3>
          <ul>
            {savedIngredients.map((ingredient, idx) => (
              <li key={idx}>
                {ingredient.name} - {ingredient.daysLeft} days left
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

/**
 * Example: Freshness Dashboard
 * Shows how to use utility functions for data processing
 */
export function FreshnessDashboard({ ingredients = [] }) {
  // Get statistics
  const urgentCount = filterIngredientsNearExpiry(ingredients, 2).length;
  const freshCount = filterFreshIngredients(ingredients, 5).length;
  const expiringCount = filterIngredientsNearExpiry(ingredients, 5).length;

  const sorted = sortIngredientsByFreshness(ingredients);

  return (
    <div className="dashboard">
      <h2>Freshness Dashboard</h2>

      {/* Stats */}
      <div className="stats-grid">
        <div className="stat-card urgent">
          <h4>Urgent Use</h4>
          <p className="number">{urgentCount}</p>
          <p>Use today</p>
        </div>

        <div className="stat-card warning">
          <h4>Use Soon</h4>
          <p className="number">{expiringCount}</p>
          <p>Within 5 days</p>
        </div>

        <div className="stat-card fresh">
          <h4>Fresh Stock</h4>
          <p className="number">{freshCount}</p>
          <p>Over 5 days</p>
        </div>

        <div className="stat-card total">
          <h4>Total Items</h4>
          <p className="number">{ingredients.length}</p>
          <p>In fridge</p>
        </div>
      </div>

      {/* Timeline */}
      <div className="timeline">
        <h3>Expiration Timeline</h3>
        {sorted.map((ingredient, idx) => (
          <div key={idx} className="timeline-item">
            <div
              className="timeline-marker"
              style={{
                backgroundColor: getFreshnessColor(ingredient.daysLeft),
              }}
            ></div>
            <div className="timeline-content">
              <h4>{ingredient.name}</h4>
              <p>{getFreshnessLabel(ingredient.daysLeft)}</p>
              <p className="days">{ingredient.daysLeft} days remaining</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Example: Image Upload with Validation
 */
export function ImageUploadExample() {
  const [preview, setPreview] = useState(null);
  const [error, setError] = useState(null);

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Validate
    const validation = validateImage(file);
    if (!validation.valid) {
      setError(validation.error);
      setPreview(null);
      return;
    }

    setError(null);

    // Show preview
    const reader = new FileReader();
    reader.onload = (event) => {
      setPreview(event.target.result);
    };
    reader.readAsDataURL(file);
  };

  return (
    <div>
      <input
        type="file"
        accept="image/*"
        onChange={handleFileSelect}
      />
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {preview && (
        <img src={preview} alt="Preview" style={{ maxWidth: '200px' }} />
      )}
    </div>
  );
}

export default AdvancedIngredientManager;
