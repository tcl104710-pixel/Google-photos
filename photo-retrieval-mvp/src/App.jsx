import { BrowserRouter, Route, Routes } from 'react-router-dom';
import Login from './pages/Login';
import AuthCallback from './pages/AuthCallback';
import Session from './pages/Session';

function App() {
  return (
    <BrowserRouter>
      <div className="app-container">
        <Routes>
          <Route path="/" element={<Login />} />
          <Route path="/auth/callback" element={<AuthCallback />} />
          <Route path="/session" element={<Session />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
