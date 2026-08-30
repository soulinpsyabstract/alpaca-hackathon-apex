import React, { useState, useEffect } from 'react';

export default function Dashboard() {
  const [account, setAccount] = useState(null);
  const [positions, setPositions] = useState([]);
  const [signal, setSignal] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const accRes = await fetch('http://localhost:8000/tools/get_account');
        const acc = await accRes.json();
        setAccount(acc);

        const posRes = await fetch('http://localhost:8000/tools/get_positions');
        const pos = await posRes.json();
        setPositions(pos.positions || []);

        const sigRes = await fetch('http://localhost:8000/tools/get_signal');
        const sig = await sigRes.json();
        setSignal(sig);
      } catch (err) {
        setError('Bot offline');
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{
      background: '#0a0e27',
      minHeight: '100vh',
      padding: '20px',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      color: '#e0e0e0'
    }}>
      {/* Header */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: '40px',
        paddingBottom: '20px',
        borderBottom: '1px solid rgba(255,255,255,0.1)'
      }}>
        <h1 style={{ margin: 0, fontSize: '32px', fontWeight: '700', color: '#fff' }}>
          Trading Bot
        </h1>
        <div style={{ 
          padding: '8px 16px', 
          background: '#1a4d2e', 
          borderRadius: '6px',
          color: '#4ade80',
          fontSize: '14px',
          fontWeight: '500'
        }}>
          ● Live
        </div>
      </div>

      {error && <p style={{ color: '#ff4444', marginBottom: '20px' }}>{error}</p>}

      {/* Main Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px', marginBottom: '40px' }}>
        {/* Balance Card */}
        <div style={{
          background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
          border: '1px solid #2d3561',
          borderRadius: '12px',
          padding: '20px',
          cursor: 'pointer',
          transition: 'all 0.3s',
          ':hover': { borderColor: '#5b63d8' }
        }}>
          <p style={{ margin: '0 0 10px 0', fontSize: '12px', color: '#888', textTransform: 'uppercase', letterSpacing: '1px' }}>Balance</p>
          <p style={{ margin: 0, fontSize: '28px', fontWeight: '700', color: '#fff' }}>
            {account ? `$${account.cash.toFixed(0)}` : '-'}
          </p>
        </div>

        {/* Buying Power Card */}
        <div style={{
          background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
          border: '1px solid #2d3561',
          borderRadius: '12px',
          padding: '20px'
        }}>
          <p style={{ margin: '0 0 10px 0', fontSize: '12px', color: '#888', textTransform: 'uppercase', letterSpacing: '1px' }}>Power</p>
          <p style={{ margin: 0, fontSize: '28px', fontWeight: '700', color: '#fff' }}>
            {account ? `$${account.buying_power.toFixed(0)}` : '-'}
          </p>
        </div>

        {/* Signal Card */}
        <div style={{
          background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
          border: '1px solid #2d3561',
          borderRadius: '12px',
          padding: '20px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center'
        }}>
          <p style={{ margin: '0 0 10px 0', fontSize: '12px', color: '#888', textTransform: 'uppercase', letterSpacing: '1px' }}>Signal</p>
          <p style={{ 
            margin: 0, 
            fontSize: '24px', 
            fontWeight: '700', 
            color: signal?.signal === 'BULLISH' ? '#4ade80' : signal?.signal === 'BEARISH' ? '#ff6b6b' : '#888'
          }}>
            {signal?.signal || 'NONE'}
          </p>
        </div>
      </div>

      {/* Positions Table */}
      <div style={{
        background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
        border: '1px solid #2d3561',
        borderRadius: '12px',
        padding: '20px'
      }}>
        <h3 style={{ margin: '0 0 20px 0', fontSize: '18px', fontWeight: '600', color: '#fff' }}>Open Positions</h3>
        
        {positions.length === 0 ? (
          <p style={{ color: '#666', margin: 0 }}>No open positions</p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #2d3561' }}>
                  <th style={{ textAlign: 'left', padding: '12px 0', color: '#888', fontSize: '12px', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Symbol</th>
                  <th style={{ textAlign: 'right', padding: '12px 0', color: '#888', fontSize: '12px', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Qty</th>
                  <th style={{ textAlign: 'right', padding: '12px 0', color: '#888', fontSize: '12px', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Entry</th>
                  <th style={{ textAlign: 'right', padding: '12px 0', color: '#888', fontSize: '12px', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Price</th>
                  <th style={{ textAlign: 'right', padding: '12px 0', color: '#888', fontSize: '12px', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px' }}>P&L</th>
                </tr>
              </thead>
              <tbody>
                {positions.map(p => (
                  <tr key={p.symbol} style={{ borderBottom: '1px solid #2d3561' }}>
                    <td style={{ padding: '16px 0', color: '#fff', fontWeight: '600', fontSize: '14px' }}>{p.symbol}</td>
                    <td style={{ textAlign: 'right', padding: '16px 0', color: '#e0e0e0' }}>{p.qty}</td>
                    <td style={{ textAlign: 'right', padding: '16px 0', color: '#e0e0e0' }}>${p.avg_entry_price.toFixed(2)}</td>
                    <td style={{ textAlign: 'right', padding: '16px 0', color: '#e0e0e0' }}>${p.current_price.toFixed(2)}</td>
                    <td style={{ 
                      textAlign: 'right', 
                      padding: '16px 0', 
                      color: p.unrealized_pl >= 0 ? '#4ade80' : '#ff6b6b',
                      fontWeight: '600'
                    }}>
                      ${p.unrealized_pl.toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
