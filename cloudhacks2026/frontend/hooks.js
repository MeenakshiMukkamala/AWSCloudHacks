// Custom React hooks for Scrapless

import { useState, useCallback } from 'react';
import apiClient from './api';
import { validateImage } from './utils';

/**
 * Hook for handling image upload and analysis
 * @returns {Object} - Hook methods and state
 */
export const useImageAnalysis = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [ingredients, setIngredients] = useState([]);
  const [uploadedImage, setUploadedImage] = useState(null);

  const analyzeImage = useCallback(async (file) => {
    setError(null);
    setLoading(true);

    try {
      const validation = validateImage(file);
      if (!validation.valid) {
        setError(validation.error);
        setLoading(false);
        return;
      }

      const reader = new FileReader();
      reader.onload = (event) => {
        setUploadedImage(event.target.result);
      };
      reader.readAsDataURL(file);

      const response = await apiClient.analyzeIngredients(file);
      setIngredients(response.ingredients || []);
    } catch (err) {
      setError(err.message || 'Failed to analyze image');
    } finally {
      setLoading(false);
    }
  }, []);

  const clearData = useCallback(() => {
    setUploadedImage(null);
    setIngredients([]);
    setError(null);
  }, []);

  return {
    loading,
    error,
    ingredients,
    uploadedImage,
    analyzeImage,
    clearData,
  };
};

/**
 * Hook for fetching recipe suggestions
 * @returns {Object} - Hook methods and state
 */
export const useRecipeSuggestions = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [recipes, setRecipes] = useState([]);

  const fetchRecipes = useCallback(async (ingredientNames) => {
    setError(null);
    setLoading(true);

    try {
      const response = await apiClient.getRecipeSuggestions(ingredientNames);
      setRecipes(response.recipes || []);
    } catch (err) {
      setError(err.message || 'Failed to fetch recipes');
      setRecipes([]);
    } finally {
      setLoading(false);
    }
  }, []);

  return { loading, error, recipes, fetchRecipes };
};

/**
 * Hook for managing local storage
 * @param {string} key - Storage key
 * @param {any} initialValue - Initial value
 * @returns {Array} - [value, setValue]
 */
export const useLocalStorage = (key, initialValue) => {
  const [storedValue, setStoredValue] = useState(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.error('Error reading from localStorage:', error);
      return initialValue;
    }
  });

  const setValue = useCallback(
    (value) => {
      try {
        const valueToStore =
          value instanceof Function ? value(storedValue) : value;
        setStoredValue(valueToStore);
        window.localStorage.setItem(key, JSON.stringify(valueToStore));
      } catch (error) {
        console.error('Error writing to localStorage:', error);
      }
    },
    [key, storedValue]
  );

  return [storedValue, setValue];
};

/**
 * Hook for handling debounced values
 * @param {any} value - Value to debounce
 * @param {number} delay - Delay in milliseconds
 * @returns {any} - Debounced value
 */
export const useDebounce = (value, delay = 500) => {
  const [debouncedValue, setDebouncedValue] = useState(value);

  React.useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => clearTimeout(handler);
  }, [value, delay]);

  return debouncedValue;
};

/**
 * Hook for managing async operations
 * @param {Function} asyncFunction - Async function to execute
 * @returns {Object} - State and execute function
 */
export const useAsync = (asyncFunction, immediate = true) => {
  const [state, setState] = useState({
    loading: false,
    error: null,
    data: null,
  });

  const execute = useCallback(async (...args) => {
    setState({ loading: true, error: null, data: null });
    try {
      const response = await asyncFunction(...args);
      setState({ loading: false, error: null, data: response });
      return response;
    } catch (error) {
      setState({ loading: false, error: error.message, data: null });
      throw error;
    }
  }, [asyncFunction]);

  useEffect(() => {
    if (immediate) {
      execute();
    }
  }, [execute, immediate]);

  return { ...state, execute };
};
