import { useCallback, useEffect, useState } from 'react';
import { ChannelInfo, listChannels, registerChannel, triggerFetch } from '../api';

function ChannelCard({ channel }: { channel: ChannelInfo }) {
  const [fetching, setFetching] = useState(false);
  const [lastResult, setLastResult] = useState<string>('');

  const handleFetch = useCallback(async () => {
    setFetching(true);
    try {
      const res = await triggerFetch(channel.name);
      setLastResult(res.success ? `成功: 获取 ${res.fetched} 条, 保存 ${res.saved} 条` : `失败: ${res.error}`);
    } catch {
      setLastResult('请求失败');
    } finally {
      setFetching(false);
    }
  }, [channel.name]);

  return (
    <div style={{
      background: '#161b22',
      border: '1px solid #30363d',
      borderRadius: '8px',
      padding: '16px',
    }}>
      <h3 style={{ margin: '0 0 8px', fontSize: '16px', color: '#e6edf3' }}>
        {channel.display_name}
      </h3>
      <p style={{ margin: '0 0 12px', fontSize: '13px', color: '#8b949e' }}>
        {channel.description}
      </p>

      <div style={{ display: 'flex', gap: '8px', fontSize: '12px', color: '#8b949e', marginBottom: '12px' }}>
        <span>消息数: <strong style={{ color: '#e6edf3' }}>{channel.total_messages}</strong></span>
        {channel.last_fetch_at && (
          <span>上次采集: <strong style={{ color: '#e6edf3', fontFamily: '"JetBrains Mono", monospace' }}>{channel.last_fetch_at.slice(0, 19)}</strong></span>
        )}
        {channel.last_error && (
          <span style={{ color: '#f85149' }}>{channel.last_error}</span>
        )}
      </div>

      <div style={{ display: 'flex', gap: '8px' }}>
        <button
          onClick={handleFetch}
          disabled={fetching}
          style={{
            background: fetching ? '#30363d' : '#238636',
            color: '#fff',
            border: 'none',
            borderRadius: '6px',
            padding: '6px 14px',
            fontSize: '13px',
            cursor: fetching ? 'not-allowed' : 'pointer',
          }}
        >
          {fetching ? '采集中...' : '立即采集'}
        </button>
      </div>

      {lastResult && (
        <p style={{
          marginTop: '8px',
          fontSize: '12px',
          color: lastResult.startsWith('成功') ? '#238636' : '#f85149',
          fontFamily: '"JetBrains Mono", monospace',
        }}>
          {lastResult}
        </p>
      )}
    </div>
  );
}

function RegisterForm({ onRegistered }: { onRegistered: () => void }) {
  const [name, setName] = useState('tavily');
  const [apiKey, setApiKey] = useState('');
  const [cron, setCron] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await registerChannel(name, { api_key: apiKey }, cron || undefined);
      onRegistered();
      setApiKey('');
      setCron('');
    } catch {
      alert('注册失败');
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{
      background: '#161b22',
      border: '1px solid #30363d',
      borderRadius: '8px',
      padding: '16px',
      marginBottom: '16px',
    }}>
      <h3 style={{ margin: '0 0 12px', fontSize: '14px' }}>注册渠道</h3>
      <div style={{ display: 'flex', gap: '8px', alignItems: 'end', flexWrap: 'wrap' }}>
        <label style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <span style={{ fontSize: '12px', color: '#8b949e' }}>渠道</span>
          <select
            value={name}
            onChange={(e) => setName(e.target.value)}
            style={{
              background: '#0d1117',
              border: '1px solid #30363d',
              borderRadius: '6px',
              padding: '8px',
              color: '#e6edf3',
              fontSize: '13px',
            }}
          >
            <option value="tavily">Tavily</option>
            <option value="webhook">Webhook</option>
          </select>
        </label>
        <label style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <span style={{ fontSize: '12px', color: '#8b949e' }}>API Key</span>
          <input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="输入 API Key"
            style={{
              background: '#0d1117',
              border: '1px solid #30363d',
              borderRadius: '6px',
              padding: '8px 12px',
              color: '#e6edf3',
              fontSize: '13px',
              width: '240px',
            }}
          />
        </label>
        <label style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <span style={{ fontSize: '12px', color: '#8b949e' }}>Cron (可选)</span>
          <input
            value={cron}
            onChange={(e) => setCron(e.target.value)}
            placeholder="*/30 * * * *"
            style={{
              background: '#0d1117',
              border: '1px solid #30363d',
              borderRadius: '6px',
              padding: '8px 12px',
              color: '#e6edf3',
              fontSize: '13px',
              fontFamily: '"JetBrains Mono", monospace',
              width: '140px',
            }}
          />
        </label>
        <button
          type="submit"
          style={{
            background: '#1f6feb',
            color: '#fff',
            border: 'none',
            borderRadius: '6px',
            padding: '8px 16px',
            fontSize: '13px',
            cursor: 'pointer',
          }}
        >
          注册
        </button>
      </div>
    </form>
  );
}

export default function ChannelsPage() {
  const [channels, setChannels] = useState<ChannelInfo[]>([]);

  const loadChannels = useCallback(async () => {
    try {
      const list = await listChannels();
      setChannels(list);
    } catch (err) {
      console.error('Failed to load channels:', err);
    }
  }, []);

  useEffect(() => {
    loadChannels();
  }, [loadChannels]);

  return (
    <div>
      <h1 style={{ fontSize: '20px', marginBottom: '16px' }}>渠道管理</h1>
      <RegisterForm onRegistered={loadChannels} />
      <div style={{ display: 'grid', gap: '12px', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))' }}>
        {channels.map((ch) => (
          <ChannelCard key={ch.name} channel={ch} />
        ))}
      </div>
    </div>
  );
}
