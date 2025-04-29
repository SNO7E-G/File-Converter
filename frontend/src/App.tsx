import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import {
  HomePage,
  LoginPage,
  RegisterPage,
  DashboardPage,
  ConvertPage,
  BatchConvertPage,
  HistoryPage,
  ConversionDetailPage,
  TemplatesPage,
  StatisticsPage,
  SharedPage,
  SchedulePage,
  ProfilePage,
  NotFoundPage
} from './pages';
import Layout from './components/Layout';
import GlobalShortcutProvider from './components/GlobalShortcutProvider';
import ErrorNotification from './components/ErrorNotification';
import { AuthProvider } from './context/AuthContext';
import { useAuth } from './hooks';
import { ErrorProvider } from './context/ErrorContext';

// Protected route component
const ProtectedRoute: React.FC<{ 
  children: React.ReactNode
}> = ({ children }) => {
  const { isAuthenticated, isLoading, checkAuth } = useAuth();
  
  useEffect(() => {
    // Verify authentication on protected routes
    checkAuth();
  }, [checkAuth]);
  
  // Show loading state while checking authentication
  if (isLoading) {
    return <div>Loading...</div>;
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }
  
  return <>{children}</>;
};

// Public route that redirects to dashboard if already authenticated
const PublicOnlyRoute: React.FC<{
  children: React.ReactNode
}> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();
  
  if (isLoading) {
    return <div>Loading...</div>;
  }
  
  if (isAuthenticated) {
    return <Navigate to="/app" />;
  }
  
  return <>{children}</>;
};

// Routes component separated to use auth context
const AppRoutes: React.FC = () => {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/" element={<HomePage />} />
      <Route path="/login" element={
        <PublicOnlyRoute>
          <LoginPage />
        </PublicOnlyRoute>
      } />
      <Route path="/register" element={
        <PublicOnlyRoute>
          <RegisterPage />
        </PublicOnlyRoute>
      } />
      
      {/* Protected routes */}
      <Route path="/app" element={
        <ProtectedRoute>
          <Layout />
        </ProtectedRoute>
      }>
        <Route index element={<DashboardPage />} />
        <Route path="convert" element={<ConvertPage />} />
        <Route path="batch" element={<BatchConvertPage />} />
        <Route path="schedule" element={<SchedulePage />} />
        <Route path="history" element={<HistoryPage />} />
        <Route path="history/:id" element={<ConversionDetailPage />} />
        <Route path="shared" element={<SharedPage />} />
        <Route path="templates" element={<TemplatesPage />} />
        <Route path="statistics" element={<StatisticsPage />} />
        <Route path="profile" element={<ProfilePage />} />
      </Route>
      
      {/* 404 route */}
      <Route path="/404" element={<NotFoundPage />} />
      
      {/* Catch-all route */}
      <Route path="*" element={<Navigate to="/404" replace />} />
    </Routes>
  );
};

const App: React.FC = () => {
  return (
    <ErrorProvider>
      <AuthProvider>
        <Router>
          <GlobalShortcutProvider>
            <AppRoutes />
            <ErrorNotification />
          </GlobalShortcutProvider>
        </Router>
      </AuthProvider>
    </ErrorProvider>
  );
};

export default App; 