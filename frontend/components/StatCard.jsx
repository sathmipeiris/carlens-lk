export default function StatCard({ label, value, sub, trend, loading, accent }) {
  if (loading) {
    return (
      <div className="card p-5">
        <div className="skeleton h-3 w-20 mb-4" />
        <div className="skeleton h-8 w-32 mb-2" />
        <div className="skeleton h-3 w-24" />
      </div>
    )
  }

  const trendColor =
    trend === 'up' ? '#34D399'
    : trend === 'down' ? '#FB7185'
    : '#64748B'

  return (
    <div
      className="card p-5 flex flex-col gap-2 group cursor-default"
      style={{ transition: 'transform 0.2s' }}
      onMouseEnter={e => e.currentTarget.style.transform = 'translateY(-2px)'}
      onMouseLeave={e => e.currentTarget.style.transform = 'translateY(0)'}
    >
      <span style={{ fontSize: 12, color: '#64748B', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
        {label}
      </span>
      <div className="flex items-baseline gap-2">
        <span
          style={{
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: 26,
            fontWeight: 600,
            color: accent || '#F1F5F9',
            lineHeight: 1,
          }}
        >
          {value}
        </span>
        {trend && (
          <span style={{ fontSize: 12, color: trendColor, fontWeight: 500 }}>
            {trend === 'up' ? '▲' : trend === 'down' ? '▼' : '—'}
          </span>
        )}
      </div>
      {sub && (
        <span style={{ fontSize: 13, color: '#3D5068' }}>{sub}</span>
      )}
    </div>
  )
}
