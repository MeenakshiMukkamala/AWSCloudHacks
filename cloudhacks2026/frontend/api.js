// API client for Scrapless backend

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class APIClient {
  constructor(baseURL = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  /**
   * Analyze image and extract ingredients
   * @param {File} imageFile - The image file to analyze
   * @returns {Promise<Object>} - Response with ingredients array
   */
  async analyzeIngredients(imageFile) {
    try {
      const formData = new FormData();
      formData.append('image', imageFile);

      const response = await fetch(`${this.baseURL}/api/analyze-ingredients`, {
        method: 'POST',
        body: formData,
        headers: {
          Accept: 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error analyzing ingredients:', error);
      throw new Error('Failed to analyze ingredients. Please try again.');
    }
  }

  /**
   * Get recipe suggestions based on ingredients
   * @param {Array<string>} ingredientNames - Array of ingredient names
   * @returns {Promise<Object>} - Response with recipe suggestions
   */
  async getRecipeSuggestions(ingredientNames) {
    try {
      const response = await fetch(`${this.baseURL}/api/recipes/suggest`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        body: JSON.stringify({ ingredients: ingredientNames }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching recipe suggestions:', error);
      throw new Error('Failed to get recipe suggestions.');
    }
  }

  /**
   * Get storage tips for an ingredient
   * @param {string} ingredientName - Name of the ingredient
   * @returns {Promise<Object>} - Response with storage tips
   */
  async getStorageTips(ingredientName) {
    try {
      const response = await fetch(
        `${this.baseURL}/api/ingredients/${encodeURIComponent(ingredientName)}/tips`,
        {
          method: 'GET',
          headers: {
            Accept: 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching storage tips:', error);
      throw new Error('Failed to get storage tips.');
    }
  }

  /**
   * Get user's ingredient history
   * @returns {Promise<Object>} - Response with ingredient history
   */
  async getIngredientHistory() {
    try {
      const response = await fetch(`${this.baseURL}/api/ingredients/history`, {
        method: 'GET',
        headers: {
          Accept: 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching ingredient history:', error);
      throw new Error('Failed to get ingredient history.');
    }
  }

  /**
   * Save ingredient to user's fridge
   * @param {Object} ingredient - Ingredient object to save
   * @returns {Promise<Object>} - Response confirmation
   */
  async saveIngredient(ingredient) {
    try {
      const response = await fetch(`${this.baseURL}/api/ingredients/save`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        body: JSON.stringify(ingredient),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error saving ingredient:', error);
      throw new Error('Failed to save ingredient.');
    }
  }
}

export default new APIClient();
