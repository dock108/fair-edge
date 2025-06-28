import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { PrivateRoute, PublicRoute } from './components/PrivateRoute';
import { Header } from './components/Header';
import { Footer } from './components/Footer';
import { DashboardPage } from './pages/DashboardPage';
import EducationPage from './pages/EducationPage';
import PricingPage from './pages/PricingPage';
import DisclaimerPage from './pages/DisclaimerPage';
import LoginPage from './pages/LoginPage';
import SignUpPage from './pages/SignUpPage';
import UpgradeSuccessPage from './pages/UpgradeSuccessPage';
import './styles/dashboard.css';


function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="App">
          <Header />
          
          <main className="main-content">
            <Routes>
              {/* Protected Routes - Require Authentication */}
              <Route path="/" element={
                <PrivateRoute>
                  <DashboardPage />
                </PrivateRoute>
              } />
              
              <Route path="/upgrade/success" element={
                <PrivateRoute>
                  <UpgradeSuccessPage />
                </PrivateRoute>
              } />
              
              {/* Public Routes - Accessible to Everyone */}
              <Route path="/education" element={<EducationPage />} />
              <Route path="/pricing" element={<PricingPage />} />
              <Route path="/disclaimer" element={<DisclaimerPage />} />
              
              {/* Public-Only Routes - Redirect Authenticated Users */}
              <Route path="/login" element={
                <PublicRoute>
                  <LoginPage />
                </PublicRoute>
              } />
              
              <Route path="/signup" element={
                <PublicRoute>
                  <SignUpPage />
                </PublicRoute>
              } />
              
              {/* 404 Handler */}
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
