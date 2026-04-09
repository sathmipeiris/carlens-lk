// frontend/components/PriceBreakdown.jsx
// Drop-in component — shows base price + economic adjustment waterfall

import { useState } from 'react'

function AdjRow({ label, pct, lkr, explanation, color, expanded }) {
  const [open, setOpen] = useState(false)
  const isPositive = pct >= 0
  const barColor   = isPositive ? '#F59E0B' : '#10B981'
  const barWidth   = Math.min(Math.abs(pct) * 4, 100)

  return (
    <div
      style={{
        borderBottom: '1px solid rgba(255,255,255,0.05)',
        paddingBottom: 12,
        marginBottom:  12,
      }}
    >
      <div
        className="flex items-center justify-between cursor-pointer gap-4"
        onClick={() => setOpen(!open)}
        style={{ userSelect: 'none' }}
      >
        {/* Label + bar */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div className="flex items-center justify-between mb-1.5">
            <span style={{ fontSize: 13, color: '#94A3B8', fontWeight: 500 }}>
              {label}
            </span>
            <div className="flex items-center gap-3">
              <span
                style={{
                  fontFamily: 'JetBrains Mono, monospace',
                  fontSize:   13,
                  fontWeight: 600,
                  color:      barColor,
                }}
              >
                {isPositive ? '+' : ''}{pct.toFixed(1)}%
              </span>
              <span
                style={{
                  fontFamily: 'JetBrains Mono, monospace',
                  fontSize:   12,
                  color:      barColor,
                  opacity:    0.7,
                }}
              >
                {isPositive ? '+' : ''}Rs.{lkr.toFixed(2)}L
              </span>
              <span style={{ fontSize: 12, color: '#3D5068' }}>
                {open ? '▲' : '▼'}
              </span>
            </div>
          </div>

          {/* Progress bar */}
          <div
            style={{
              height:       4,
              borderRadius: 2,
              background:   'rgba(255,255,255,0.06)',
              overflow:     'hidden',
            }}
          >
            <div
              style={{
                width:        `${barWidth}%`,
                height:       '100%',
                background:   barColor,
                borderRadius: 2,
                transition:   'width 0.6s ease',
                marginLeft:   isPositive ? 0 : 'auto',
              }}
            />
          </div>
        </div>
      </div>

      {/* Expanded explanation */}
      {open && (
        <div
          style={{
            marginTop:    10,
            padding:      '10px 14px',
            background:   'rgba(255,255,255,0.03)',
            borderRadius: 8,
            fontSize:     13,
            color:        '#64748B',
            lineHeight:   1.6,
            borderLeft:   `2px solid ${barColor}`,
          }}
        >
          {explanation}
        </div>
      )}
    </div>
  )
}

export default function PriceBreakdown({ result, loading }) {
  if (loading) {
    return (
      <div
        className="card p-7"
        style={{ border: '1px solid rgba(244,162,39,0.15)' }}
      >
        <div className="skeleton h-4 w-40 mb-6" />
        <div className="skeleton h-12 w-48 mb-2" />
        <div className="skeleton h-4 w-32 mb-8" />
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="mb-5">
            <div className="skeleton h-3 w-full mb-2" />
            <div className="skeleton h-2 w-full" />
          </div>
        ))}
      </div>
    )
  }

  if (!result) return null

  const {
    base_price,
    final_price,
    total_adjustment_pct,
    total_adjustment_lkr,
    adjustments,
    economic_context,
    car_summary,
  } = result

  const adj = adjustments || {}
  const isGain = total_adjustment_pct >= 0

  const rows = [
    {
      key:  'usd_lkr',
      icon: '💱',
      label: 'USD/LKR exchange rate',
    },
    {
      key:  'inflation',
      icon: '📈',
      label: 'Inflation depreciation',
    },
    {
      key:  'fuel',
      icon: '⛽',
      label: 'Fuel price premium',
    },
    {
      key:  'import_scarcity',
      icon: '🚗',
      label: 'Import restriction scarcity',
    },
  ]

  return (
    <div
      className="card p-7"
      style={{ border: '1px solid rgba(244,162,39,0.2)' }}
    >
      {/* Header */}
      <div
        style={{
          fontSize:      12,
          color:         '#F4A227',
          fontWeight:    600,
          textTransform: 'uppercase',
          letterSpacing: '0.08em',
          marginBottom:  20,
        }}
      >
        Economically adjusted price
      </div>

      {/* Final price */}
      <div
        style={{
          fontFamily: 'JetBrains Mono, monospace',
          fontSize:   44,
          fontWeight: 700,
          color:      '#F4A227',
          lineHeight: 1,
          marginBottom: 6,
        }}
      >
        Rs. {final_price.toFixed(1)}L
      </div>

      {/* Adjustment summary */}
      <div
        className="flex items-center gap-2 mb-8"
        style={{ fontSize: 13 }}
      >
        <span style={{ color: '#3D5068' }}>
          Base: Rs. {base_price.toFixed(1)}L
        </span>
        <span style={{ color: '#3D5068' }}>·</span>
        <span
          style={{
            color: isGain ? '#F59E0B' : '#10B981',
            fontFamily: 'JetBrains Mono, monospace',
            fontWeight: 600,
          }}
        >
          {isGain ? '+' : ''}{total_adjustment_pct.toFixed(1)}%
          ({isGain ? '+' : ''}Rs.{total_adjustment_lkr.toFixed(2)}L)
        </span>
      </div>

      {/* Waterfall rows */}
      <div
        style={{
          borderTop:   '1px solid rgba(255,255,255,0.06)',
          paddingTop:  20,
          marginBottom: 8,
        }}
      >
        <div
          style={{
            fontSize:      11,
            color:         '#2D3F58',
            textTransform: 'uppercase',
            letterSpacing: '0.06em',
            marginBottom:  16,
          }}
        >
          Adjustment breakdown — click each to expand
        </div>

        {rows.map(({ key, label }) => {
          const a = adj[key]
          if (!a) return null
          return (
            <AdjRow
              key={key}
              label={label}
              pct={a.pct || 0}
              lkr={a.lkr_lakhs || 0}
              explanation={a.explanation || ''}
            />
          )
        })}
      </div>

      {/* Live data sources */}
      {economic_context && (
        <div
          style={{
            marginTop:    20,
            padding:      '14px 16px',
            background:   'rgba(255,255,255,0.02)',
            borderRadius: 10,
            border:       '1px solid rgba(255,255,255,0.05)',
          }}
        >
          <div
            style={{
              fontSize:      11,
              color:         '#2D3F58',
              textTransform: 'uppercase',
              letterSpacing: '0.06em',
              marginBottom:  12,
            }}
          >
            Live indicators used
          </div>
          <div className="grid grid-cols-2 gap-3">
            {[
              {
                label: 'USD/LKR',
                value: `${economic_context.usd_lkr_rate?.toFixed(1)}`,
              },
              {
                label: 'Inflation',
                value: `${economic_context.inflation_rate?.toFixed(1)}%`,
              },
              {
                label: 'Petrol 92',
                value: `Rs. ${economic_context.petrol_price}`,
              },
              {
                label: 'YOM restriction',
                value: car_summary?.yom >= 2020 && car_summary?.yom <= 2023
                  ? 'Ban era ⚠' : 'Normal',
              },
            ].map(({ label, value }) => (
              <div key={label}>
                <div style={{ fontSize: 11, color: '#2D3F58' }}>{label}</div>
                <div
                  style={{
                    fontFamily: 'JetBrains Mono, monospace',
                    fontSize:   13,
                    color:      '#94A3B8',
                    fontWeight: 500,
                  }}
                >
                  {value}
                </div>
              </div>
            ))}
          </div>

          {/* Data source labels */}
          {economic_context.sources && (
            <div
              style={{
                marginTop:  12,
                fontSize:   11,
                color:      '#1E293B',
                lineHeight: 1.6,
              }}
            >
              Sources: {Object.values(economic_context.sources)
                .filter(Boolean)
                .filter((v, i, a) => a.indexOf(v) === i)
                .join(' · ')}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
