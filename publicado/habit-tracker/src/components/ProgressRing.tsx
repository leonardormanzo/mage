type Props = {
  progress: number
  size?: number
  strokeWidth?: number
  color?: string
  label?: string
}

export function ProgressRing({ progress, size = 88, strokeWidth = 8, color = '#22c55e', label }: Props) {
  const clamped = Math.min(1, Math.max(0, progress))
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference * (1 - clamped)

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--color-border)"
          strokeWidth={strokeWidth}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 300ms ease-out' }}
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className="text-lg font-semibold font-heading">{Math.round(clamped * 100)}%</span>
        {label ? <span className="text-[11px] text-text-muted">{label}</span> : null}
      </div>
    </div>
  )
}
