import { useCallback, useEffect, useState } from 'react';
import { analyzeVitality, discoverIndustries, listVitalality, searchPapers, VitalityResult, PaperResult } from '../api';

function ScoreBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div style={{ marginBottom: '4px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#8b949e' }}>
        <span>{label}</span>
        <span style={{ fontFamily: '"JetBrains Mono", monospace' }}>{value.toFixed(1)}</span>
      </div>
      <div style={{ height: '4px', background: '#21262d', borderRadius: '2px' }}>
        <div style={{ width: `${Math.min(value, 100)}%`, height: '100%', background: color, borderRadius: '2px' }} />
      </div>
    </div>
  );
}

function VitalityCard({ result, onClick }: { result: VitalityResult; onClick: () => void }) {
  const scoreColor = result.total_score >= 70 ? '#238636' : result.total_score >= 40 ? '#9e6a03' : '#f85149';
  return (
    <div
      onClick={onClick}
      style={{
        background: '#161b22',
        border: '1px solid #30363d',
        borderRadius: '8px',
        padding: '16px',
        cursor: 'pointer',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <h3 style={{ margin: 0, fontSize: '16px', color: '#e6edf3' }}>{result.industry}</h3>
        <span style={{
          fontFamily: '"JetBrains Mono", monospace',
          fontSize: '24px',
          fontWeight: 700,
          color: scoreColor,
        }}>
          {result.total_score.toFixed(1)}
        </span>
      </div>
      <div style={{ fontSize: '11px', color: '#8b949e', marginBottom: '8px' }}>
        消息数: {result.message_count} | 分析: {result.analyzed_at?.slice(0, 19)}
      </div>
      <ScoreBar label="活跃度" value={result.activity_score} color="#58a6ff" />
      <ScoreBar label="情感" value={result.sentiment_score} color="#238636" />
      <ScoreBar label="多样性" value={result.diversity_score} color="#9e6a03" />
      <ScoreBar label="趋势" value={result.trend_score} color="#1f6feb" />
    </div>
  );
}

function PaperCard({ paper }: { paper: PaperResult }) {
  return (
    <div style={{
      background: '#161b22',
      border: '1px solid #30363d',
      borderRadius: '8px',
      padding: '12px',
      marginBottom: '8px',
    }}>
      <h4 style={{ margin: '0 0 4px', fontSize: '14px', color: '#58a6ff' }}>
        {paper.url ? (
          <a href={paper.url} target="_blank" rel="noreferrer" style={{ color: 'inherit', textDecoration: 'none' }}>
            {paper.title}
          </a>
        ) : paper.title}
      </h4>
      <p style={{ margin: 0, fontSize: '12px', color: '#8b949e' }}>
        {paper.abstract?.slice(0, 150)}{paper.abstract?.length > 150 ? '...' : ''}
      </p>
    </div>
  );
}

export default function VitalityPage() {
  const [industries, setIndustries] = useState<VitalityResult[]>([]);
  const [selectedIndustry, setSelectedIndustry] = useState<string>('');
  const [industryInput, setIndustryInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [discovering, setDiscovering] = useState(false);
  const [papers, setPapers] = useState<PaperResult[]>([]);
  const [selectedResult, setSelectedResult] = useState<VitalityResult | null>(null);

  const loadVitality = useCallback(async () => {
    try {
      const res = await listVitalality();
      setIndustries(res.industries);
    } catch (err) {
      console.error('Failed to load vitality:', err);
    }
  }, []);

  useEffect(() => {
    loadVitality();
  }, [loadVitality]);

  const handleAnalyze = async () => {
    if (!industryInput.trim()) return;
    setLoading(true);
    try {
      const result = await analyzeVitality(industryInput);
      if ('error' in result) {
        alert(result.error);
      } else {
        setSelectedResult(result);
        loadVitality();
      }
    } catch {
      alert('分析请求失败');
    } finally {
      setLoading(false);
    }
  };

  const handleDiscover = async () => {
    setDiscovering(true);
    try {
      const res = await discoverIndustries();
      if (res.industries?.length > 0) {
        setIndustryInput(res.industries[0].industry);
      }
    } catch {
      alert('行业发现失败');
    } finally {
      setDiscovering(false);
    }
  };

  const handleSelectIndustry = async (industry: string) => {
    setSelectedIndustry(industry);
    try {
      const res = await searchPapers(industry);
      setPapers(res.papers);
    } catch {
      setPapers([]);
    }
  };

  return (
    <div>
      <h1 style={{ fontSize: '20px', marginBottom: '16px' }}>行业活力指数</h1>

      <div style={{
        background: '#161b22',
        border: '1px solid #30363d',
        borderRadius: '8px',
        padding: '16px',
        marginBottom: '16px',
      }}>
        <div style={{ display: 'flex', gap: '8px' }}>
          <input
            type="text"
            value={industryInput}
            onChange={(e) => setIndustryInput(e.target.value)}
            placeholder="输入行业关键词..."
            style={{
              flex: 1,
              background: '#0d1117',
              border: '1px solid #30363d',
              borderRadius: '6px',
              padding: '8px 12px',
              color: '#e6edf3',
              fontSize: '13px',
              outline: 'none',
            }}
            onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
          />
          <button
            onClick={handleAnalyze}
            disabled={loading}
            style={{
              background: loading ? '#30363d' : '#1f6feb',
              color: '#fff',
              border: 'none',
              borderRadius: '6px',
              padding: '8px 16px',
              fontSize: '13px',
              cursor: loading ? 'not-allowed' : 'pointer',
            }}
          >
            {loading ? '分析中...' : '分析'}
          </button>
          <button
            onClick={handleDiscover}
            disabled={discovering}
            style={{
              background: discovering ? '#30363d' : '#238636',
              color: '#fff',
              border: 'none',
              borderRadius: '6px',
              padding: '8px 16px',
              fontSize: '13px',
              cursor: discovering ? 'not-allowed' : 'pointer',
            }}
          >
            {discovering ? '发现中...' : '自动发现'}
          </button>
        </div>
      </div>

      {selectedResult && (
        <div style={{
          background: '#161b22',
          border: '1px solid #30363d',
          borderRadius: '8px',
          padding: '16px',
          marginBottom: '16px',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ margin: 0, fontSize: '18px', color: '#e6edf3' }}>{selectedResult.industry}</h3>
            <span style={{
              fontFamily: '"JetBrains Mono", monospace',
              fontSize: '32px',
              fontWeight: 700,
              color: selectedResult.total_score >= 70 ? '#238636' : selectedResult.total_score >= 40 ? '#9e6a03' : '#f85149',
            }}>
              {selectedResult.total_score.toFixed(1)}
            </span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginTop: '12px' }}>
            <ScoreBar label="活跃度" value={selectedResult.activity_score} color="#58a6ff" />
            <ScoreBar label="情感倾向" value={selectedResult.sentiment_score} color="#238636" />
            <ScoreBar label="话题多样性" value={selectedResult.diversity_score} color="#9e6a03" />
            <ScoreBar label="时间趋势" value={selectedResult.trend_score} color="#1f6feb" />
          </div>
        </div>
      )}

      {industries.length > 0 && (
        <>
          <h2 style={{ fontSize: '16px', marginBottom: '12px', color: '#8b949e' }}>已分析行业</h2>
          <div style={{ display: 'grid', gap: '12px', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))' }}>
            {industries.map((ind) => (
              <VitalityCard
                key={ind.industry}
                result={ind}
                onClick={() => handleSelectIndustry(ind.industry)}
              />
            ))}
          </div>
        </>
      )}

      {selectedIndustry && (
        <div style={{ marginTop: '24px' }}>
          <h2 style={{ fontSize: '16px', marginBottom: '12px', color: '#8b949e' }}>
            相关论文 — {selectedIndustry}
          </h2>
          {papers.length > 0 ? (
            papers.map((p, i) => <PaperCard key={i} paper={p} />)
          ) : (
            <p style={{ color: '#8b949e', textAlign: 'center', padding: '24px 0' }}>暂无论文数据</p>
          )}
        </div>
      )}
    </div>
  );
}
