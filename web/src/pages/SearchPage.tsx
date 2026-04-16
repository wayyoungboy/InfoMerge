import { useState } from 'react';
import { hybridSearch, SearchResult } from '../api';

function ResultCard({ result }: { result: SearchResult }) {
  return (
    <div style={{
      background: '#161b22',
      border: '1px solid #30363d',
      borderRadius: '8px',
      padding: '16px',
      marginBottom: '8px',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
        <h3 style={{ margin: 0, fontSize: '16px', color: '#58a6ff' }}>
          {result.url ? (
            <a href={result.url} target="_blank" rel="noreferrer" style={{ color: 'inherit', textDecoration: 'none' }}>
              {result.title}
            </a>
          ) : (
            result.title
          )}
        </h3>
        {result.score !== null && (
          <span style={{
            fontFamily: '"JetBrains Mono", monospace',
            fontSize: '12px',
            color: '#238636',
            background: '#0d1117',
            padding: '2px 8px',
            borderRadius: '4px',
          }}>
            {result.score.toFixed(3)}
          </span>
        )}
      </div>
      <p style={{ margin: '8px 0', fontSize: '14px', color: '#8b949e' }}>
        {result.content.slice(0, 200)}{result.content.length > 200 ? '...' : ''}
      </p>
      <div style={{ display: 'flex', gap: '12px', fontSize: '12px', color: '#8b949e' }}>
        <span style={{
          background: '#21262d',
          padding: '2px 8px',
          borderRadius: '4px',
          fontFamily: '"JetBrains Mono", monospace',
        }}>
          {result.channel}
        </span>
        {result.author && <span>{result.author}</span>}
        {result.published_at && <span>{result.published_at.slice(0, 10)}</span>}
      </div>
    </div>
  );
}

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    try {
      const res = await hybridSearch(query, undefined, undefined, 50);
      setResults(res.results);
      setTotal(res.total);
    } catch (err) {
      console.error('Search failed:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 style={{ fontSize: '20px', marginBottom: '16px' }}>热点搜索</h1>
      <form onSubmit={handleSearch} style={{ display: 'flex', gap: '8px', marginBottom: '24px' }}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="输入搜索关键词..."
          style={{
            flex: 1,
            background: '#0d1117',
            border: '1px solid #30363d',
            borderRadius: '6px',
            padding: '10px 14px',
            color: '#e6edf3',
            fontSize: '14px',
            outline: 'none',
          }}
          onFocus={(e) => (e.target.style.borderColor = '#1f6feb')}
          onBlur={(e) => (e.target.style.borderColor = '#30363d')}
        />
        <button
          type="submit"
          disabled={loading}
          style={{
            background: loading ? '#30363d' : '#1f6feb',
            color: '#fff',
            border: 'none',
            borderRadius: '6px',
            padding: '10px 20px',
            fontSize: '14px',
            cursor: loading ? 'not-allowed' : 'pointer',
          }}
        >
          {loading ? '搜索中...' : '搜索'}
        </button>
      </form>

      {total > 0 && (
        <p style={{ fontSize: '12px', color: '#8b949e', marginBottom: '12px' }}>
          找到 {total} 条结果
        </p>
      )}

      {results.length === 0 && query && !loading && (
        <p style={{ color: '#8b949e', textAlign: 'center', padding: '48px 0' }}>
          未找到相关结果
        </p>
      )}

      {results.map((r) => (
        <ResultCard key={r.id} result={r} />
      ))}
    </div>
  );
}
