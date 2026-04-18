import { useEffect } from 'react';

export const useAsync = (asyncFunction, immediate = false) => {
  const [state, setState] = React.useState({
    loading: false,
    error: null,
    data: null,
  });

  const execute = React.useCallback(async (...args) => {
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
