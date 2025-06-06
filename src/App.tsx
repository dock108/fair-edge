import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './hooks/useAuth';
import Navbar from './components/Navbar';
import DashboardPage from './pages/DashboardPage';
import EducationPage from './pages/EducationPage';
import PricingPage from './pages/PricingPage';
import DisclaimerPage from './pages/DisclaimerPage';

// Import CSS files
import './styles/_tokens.css';
import './styles/_layout.css';
import './styles/dashboard.css';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <div className="App">
          <Navbar />
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/education" element={<EducationPage />} />
            <Route path="/pricing" element={<PricingPage />} />
            <Route path="/disclaimer" element={<DisclaimerPage />} />
            {/* TODO: Add other routes as needed (login, account, admin) */}
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
}

// Simple 404 page component
const NotFoundPage: React.FC = () => {
  return (
    <div className="content-wrap">
      <div className="text-center py-5">
        <i className="fas fa-exclamation-triangle fa-3x text-warning mb-3"></i>
        <h1>404 - Page Not Found</h1>
        <p className="text-muted">The page you're looking for doesn't exist.</p>
        <a href="/" className="btn btn-primary">
          <i className="fas fa-home me-1"></i>
          Go Home
        </a>
      </div>
    </div>
  );
};

export default App; 