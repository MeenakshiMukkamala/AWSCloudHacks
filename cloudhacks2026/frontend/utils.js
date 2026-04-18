// Utility functions for Scrapless

export const getFreshnessColor = (daysLeft) => {
  if (daysLeft > 5) return '#10b981'; // Green
  if (daysLeft > 2) return '#f59e0b'; // Amber
  return '#ef4444'; // Red
};

export const getFreshnessLabel = (daysLeft) => {
  if (daysLeft > 5) return 'Fresh';
  if (daysLeft > 2) return 'Use Soon';
  return 'Use Today';
};

export const formatDate = (days) => {
  if (days === 0) return 'Today';
  if (days === 1) return 'Tomorrow';
  return `In ${days} days`;
};

export const isNearExpiry = (daysLeft) => {
  return daysLeft <= 2;
};

export const isExpired = (daysLeft) => {
  return daysLeft < 0;
};

export const calculateFreshnessPercentage = (daysLeft, totalDays = 10) => {
  return Math.min((daysLeft / totalDays) * 100, 100);
};

export const sortIngredientsByFreshness = (ingredients) => {
  return [...ingredients].sort((a, b) => a.daysLeft - b.daysLeft);
};

export const filterIngredientsNearExpiry = (ingredients, days = 2) => {
  return ingredients.filter((ingredient) => ingredient.daysLeft <= days);
};

export const filterFreshIngredients = (ingredients, days = 5) => {
  return ingredients.filter((ingredient) => ingredient.daysLeft > days);
};

export const getRecipeString = (recipes) => {
  if (!recipes || recipes.length === 0) return 'No suggestions available';
  return recipes.join(', ');
};

export const validateImage = (file) => {
  const validTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'];
  const maxSize = 5 * 1024 * 1024; // 5MB

  if (!validTypes.includes(file.type)) {
    return {
      valid: false,
      error: 'Invalid image format. Please use JPG, PNG, WebP, or GIF.',
    };
  }

  if (file.size > maxSize) {
    return {
      valid: false,
      error: 'Image size too large. Please use an image smaller than 5MB.',
    };
  }

  return { valid: true };
};

export const uploadImage = async (file, apiUrl = '/api/analyze-ingredients') => {
  try {
    const formData = new FormData();
    formData.append('image', file);

    const response = await fetch(apiUrl, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();
    return {
      success: true,
      data: data.ingredients || [],
    };
  } catch (error) {
    console.error('Error uploading image:', error);
    return {
      success: false,
      error: error.message || 'Failed to analyze image',
    };
  }
};
