import React, { createContext, useState, useCallback, ReactNode } from 'react';

// Define error severity levels
export type ErrorSeverity = 'error' | 'warning' | 'info' | 'success';

// Define error notification type
export interface ErrorNotification {
  id: string;
  message: string;
  severity: ErrorSeverity;
  details?: string;
  timestamp: Date;
  autoDismiss?: boolean;
  dismissAfter?: number; // milliseconds
}

// Define context type
interface ErrorContextType {
  errors: ErrorNotification[];
  addError: (message: string, severity?: ErrorSeverity, details?: string, autoDismiss?: boolean) => string;
  removeError: (id: string) => void;
  clearErrors: () => void;
}

// Create error context with default values
export const ErrorContext = createContext<ErrorContextType>({
  errors: [],
  addError: () => '',
  removeError: () => {},
  clearErrors: () => {},
});

// Props for the provider component
interface ErrorProviderProps {
  children: ReactNode;
}

export const ErrorProvider: React.FC<ErrorProviderProps> = ({ children }) => {
  const [errors, setErrors] = useState<ErrorNotification[]>([]);

  // Generate a unique ID for each error
  const generateId = (): string => {
    return Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
  };

  // Add a new error
  const addError = useCallback(
    (
      message: string, 
      severity: ErrorSeverity = 'error', 
      details?: string, 
      autoDismiss = severity !== 'error'
    ): string => {
      const id = generateId();
      const newError: ErrorNotification = {
        id,
        message,
        severity,
        details,
        timestamp: new Date(),
        autoDismiss,
        dismissAfter: autoDismiss ? (severity === 'error' ? 8000 : 5000) : undefined,
      };

      setErrors(prevErrors => [...prevErrors, newError]);

      // Auto-dismiss if specified
      if (autoDismiss && newError.dismissAfter) {
        setTimeout(() => {
          removeError(id);
        }, newError.dismissAfter);
      }

      return id;
    },
    []
  );

  // Remove an error by ID
  const removeError = useCallback((id: string) => {
    setErrors(prevErrors => prevErrors.filter(error => error.id !== id));
  }, []);

  // Clear all errors
  const clearErrors = useCallback(() => {
    setErrors([]);
  }, []);

  return (
    <ErrorContext.Provider
      value={{
        errors,
        addError,
        removeError,
        clearErrors,
      }}
    >
      {children}
    </ErrorContext.Provider>
  );
};

// Custom hook for using the error context
export const useError = () => {
  const context = React.useContext(ErrorContext);
  if (context === undefined) {
    throw new Error('useError must be used within an ErrorProvider');
  }
  return context;
}; 