import React, { useState, useEffect } from 'react';

export default function Dashboard() {
  const [account, setAccount] = useState(null);
  const [positions, setPositions] = useState([]);
  const [signal, setSignal] = useState(null);
  const [error, setError] = useState(null);
  const [closeQty, setCloseQty] = useState({});
  const [closedSymbols, setClosedSymbols] = useState([]);

  const fetchData = async () => {
    try {
      const accRes = await fetch('http://localhost:8000/tools/get_account');
      const acc = await accRes.json();
      setAccount(acc);

      const posRes = await fetch('http://localhost:8000/tools/get_positions');
      const pos = await posRes.json();
      const filtered = (pos.positions || []).filter(p => !closedSymbols.includes(p.symbol));
      setPositions(filtered);

      const sigRes = await fetch('http://localhost:8000/tools/get_signal');
      const sig = await sigRes.json();
      setSignal(sig);
    } catch (err) {
      setError('Bot offline');
    }
  };

  const closePosition = async (symbol, qty) => {
    setClosedSymbols([...closedSymbols, symbol]);
    setPositions(positions.filter(p => p.symbol !== symbol));
    try {
      const url = `http://localhost:8000/tools/place_order?symbol=${symbol}&qty=${qty}&side=sell`;
      await fetch(url, { method: 'POST' });
      return;
    } catch (err) {
      alert('Error closing position');
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const openPositions = positions.filter(p => {
    const qty = parseFloat(p.qty);
    return qty && qty > 0.00001;
  });

  return (
    <div style={{
      background: '#0a0e27',
      minHeight: '100vh',
      padding: '20px',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      color: '#e0e0e0'
    }}>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: '40px',
        paddingBottom: '20px',
        borderBottom: '1px solid rgba(255,255,255,0.1)'
      }}>
        <h1 style={{ margin: 0, fontSize: '32px', fontWeight: '700', color: '#fff' }}>Alpaca Bot</h1>
        <button onClick={fetchData} style={{ padding: '8px 16px', background: '#4ade80', color: '#000', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: '600' }}>Refresh</button>
      </div>

      {account && (
        <div style={{ marginBottom: '40px' }}>
          <h2 style={{ fontSize: '20px', marginBottom: '16px' }}>Account</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
            <div style={{ background: '#1a1f3a', padding: '16px', borderRadius: '8px', border: '1px solid #2d3561' }}>
              <div style={{ fontSize: '12px', color: '#999' }}>Balance</div>
              <div style={{ fontSize: '24px', fontWeight: '700' }}>${account.cash.toFixed(2)}</div>
            </div>
            <div style={{ background: '#1a1f3a', padding: '16px', borderRadius: '8px', border: '1px solid #2d3561' }}>
              <div style={{ fontSize: '12px', color: '#999' }}>Buying Power</div>
              <div style={{ fontSize: '24px', fontWeight: '700' }}>${account.buying_power.toFixed(2)}</div>
            </div>
            <div style={{ background: '#1a1f3a', padding: '16px', borderRadius: '8px', border: '1px solid #2d3561' }}>
              <div style={{ fontSize: '12px', color: '#999' }}>Equity</div>
              <div style={{ fontSize: '24px', fontWeight: '700' }}>${account.equity.toFixed(2)}</div>
            </div>
            <div style={{ background: '#1a1f3a', padding: '16px', borderRadius: '8px', border: '1px solid #2d3561' }}>
              <div style={{ fontSize: '12px', color: '#999' }}>Status</div>
              <div style={{ fontSize: '24px', fontWeight: '700', color: '#4ade80' }}>{account.status}</div>
            </div>
          </div>
        </div>
      )}

      {openPositions.length > 0 && (
        <div style={{ background: '#1a1f3a', padding: '24px', borderRadius: '8px', border: '1px solid #2d3561' }}>
          <h3 style={{ margin: '0 0 16px 0', fontSize: '18px', fontWeight: '600' }}>Open Positions</h3>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #4ade80' }}>
                <th style={{ textAlign: 'left', padding: '16px 0', fontSize: '12px', color: '#999' }}>Symbol</th>
                <th style={{ textAlign: 'left', padding: '16px 0', fontSize: '12px', color: '#999' }}>Side</th>
                <th style={{ textAlign: 'right', padding: '16px 0', fontSize: '12px', color: '#999' }}>Qty</th>
                <th style={{ textAlign: 'right', padding: '16px 0', fontSize: '12px', color: '#999' }}>Entry</th>
                <th style={{ textAlign: 'right', padding: '16px 0', fontSize: '12px', color: '#999' }}>Current</th>
                <th style={{ textAlign: 'right', padding: '16px 0', fontSize: '12px', color: '#999' }}>PnL</th>
                <th style={{ textAlign: 'center', padding: '16px 0', fontSize: '12px', color: '#999' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {openPositions.map(p => (
                <tr key={p.symbol} style={{ borderBottom: '1px solid #2d3561' }}>
                  <td style={{ padding: '16px 0', color: '#fff', fontWeight: '600', fontSize: '14px' }}>{p.symbol}</td>
                  <td style={{ padding: '16px 0', color: p.side === 'long' ? '#4ade80' : '#ff6b6b', fontWeight: '600' }}>{p.side.toUpperCase()}</td>
                  <td style={{ textAlign: 'right', padding: '16px 0', color: '#e0e0e0' }}>{p.qty.toFixed(5)}</td>
                  <td style={{ textAlign: 'right', padding: '16px 0', color: '#e0e0e0' }}>${p.avg_entry_price.toFixed(2)}</td>
                  <td style={{ textAlign: 'right', padding: '16px 0', color: '#e0e0e0' }}>${p.current_price.toFixed(2)}</td>
                  <td style={{ textAlign: 'right', padding: '16px 0', color: p.unrealized_pl >= 0 ? '#4ade80' : '#ff6b6b', fontWeight: '600' }}>${p.unrealized_pl.toFixed(2)}</td>
                  <td style={{ textAlign: 'center', padding: '16px 0' }}>
                    <input type="number" step="0.00001" max={p.qty} placeholder="qty" value={closeQty[p.symbol] || ''} onChange={(e) => setCloseQty({...closeQty, [p.symbol]: e.target.value})} style={{ width: '60px', padding: '4px', marginRight: '8px', borderRadius: '4px', border: '1px solid #2d3561', background: '#1a1f3a', color: '#fff' }} />
                    <button onClick={() => closePosition(p.symbol, parseFloat(closeQty[p.symbol]) || p.qty)} style={{ padding: '6px 12px', background: '#ff6b6b', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '12px' }}>Close</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {openPositions.length === 0 && <div style={{ fontSize: '16px', color: '#999', marginTop: '20px' }}>No open positions</div>}
    </div>
  );
}
