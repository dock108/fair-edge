import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { Header } from './components/Header';
import { Footer } from './components/Footer';
import { DashboardPage } from './pages/DashboardPage';
import EducationPage from './pages/EducationPage';
import PricingPage from './pages/PricingPage';
import DisclaimerPage from './pages/DisclaimerPage';
import LoginPage from './pages/LoginPage';
import SignUpPage from './pages/SignUpPage';
import './styles/dashboard.css';

// Simple success page component
const UpgradeSuccessPage = () => (
  <div className="main-container">
    <div className="text-center" style={{ padding: '4rem 2rem' }}>
      <div style={{ marginBottom: '2rem' }}>
        <i className="fas fa-crown" style={{ fontSize: '4rem', color: '#10b981' }}></i>
      </div>
      <h1 style={{ color: '#1e293b', marginBottom: '1rem' }}>Welcome to Premium!</h1>
      <p style={{ color: '#64748b', marginBottom: '2rem', fontSize: '1.125rem' }}>
        Your subscription is now active. You have access to all premium features including player props and alternate lines.
      </p>
      <a href="/" className="btn btn-primary" style={{ textDecoration: 'none' }}>
        <i className="fas fa-chart-line" style={{ marginRight: '0.5rem' }}></i>
        View Premium Opportunities
      </a>
    </div>
  </div>
);

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="App">
          <Header />
          
          <main className="main-content">
            <Routes>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/education" element={<EducationPage />} />
              <Route path="/pricing" element={<PricingPage />} />
              <Route path="/disclaimer" element={<DisclaimerPage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/signup" element={<SignUpPage />} />
              <Route path="/upgrade/success" element={<UpgradeSuccessPage />} />
              <Route path="*" element={
                <div className="container mt-4">
                  <div className="text-center">
                    <h1>404 - Page Not Found</h1>
                    <p>The page you're looking for doesn't exist.</p>
                  </div>
                </div>
              } />
            </Routes>
          </main>
          
          <Footer />
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
