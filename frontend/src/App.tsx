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
