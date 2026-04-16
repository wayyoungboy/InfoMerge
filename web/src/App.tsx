import { BrowserRouter, Link, Route, Routes, useLocation } from 'react-router-dom';
import SearchPage from './pages/SearchPage';
import ChannelsPage from './pages/ChannelsPage';
import VitalityPage from './pages/VitalityPage';

function Header() {
  const location = useLocation();
  const navStyle = (path: string) => ({
    color: location.pathname === path ? '#58a6ff' : '#8b949e',
    textDecoration: 'none',
    fontSize: '14px' as const,
  });
  return (
    <header style={{
      background: '#161b22',
      borderBottom: '1px solid #30363d',
      padding: '12px 24px',
      display: 'flex',
      alignItems: 'center',
      gap: '24px',
    }}>
      <span style={{ color: '#e6edf3', fontWeight: 700, fontSize: '18px' }}>
        InfoMerge
      </span>
      <nav style={{ display: 'flex', gap: '16px' }}>
        <Link to="/" style={navStyle('/')}>搜索</Link>
        <Link to="/vitality" style={navStyle('/vitality')}>活力指数</Link>
        <Link to="/channels" style={navStyle('/channels')}>渠道管理</Link>
      </nav>
    </header>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <div style={{
        minHeight: '100vh',
        background: '#0d1117',
        color: '#e6edf3',
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      }}>
        <Header />
        <main style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
          <Routes>
            <Route path="/" element={<SearchPage />} />
            <Route path="/vitality" element={<VitalityPage />} />
            <Route path="/channels" element={<ChannelsPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
