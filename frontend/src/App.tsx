import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { DashboardPage } from './pages/DashboardPage';
import EducationPage from './pages/EducationPage';
import PricingPage from './pages/PricingPage';
import DisclaimerPage from './pages/DisclaimerPage';
import './styles/dashboard.css';

function App() {
  // For now, we'll use a simple user state (later we can add proper auth)
  const user = null; // Will be replaced with proper auth context

  const handleLogout = () => {
    // TODO: Implement logout logic
    console.log('Logout clicked');
  };

  return (
    <Router>
      <div className="App">
        <Navbar user={user} onLogout={handleLogout} />
        
        <main>
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/education" element={<EducationPage />} />
            <Route path="/pricing" element={<PricingPage />} />
            <Route path="/disclaimer" element={<DisclaimerPage />} />
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
      </div>
    </Router>
  );
}

export default App;
