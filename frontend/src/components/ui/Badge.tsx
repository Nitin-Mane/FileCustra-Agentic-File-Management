import React from 'react';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  color?: 'cyan' | 'violet' | 'mint' | 'coral' | 'safe' | 'warning' | 'danger' | 'info';
  size?: 'sm' | 'md';
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  color = 'cyan',
  size = 'md',
  className = '',
  style = {},
  ...props
}) => {
  const getColorStyle = (): React.CSSProperties => {
    switch (color) {
      case 'violet':
        return { background: 'rgba(139, 92, 246, 0.15)', color: 'var(--accent-violet)', border: '1px solid rgba(139, 92, 246, 0.3)' };
      case 'mint':
        return { background: 'rgba(52, 211, 153, 0.15)', color: 'var(--accent-mint)', border: '1px solid rgba(52, 211, 153, 0.3)' };
      case 'coral':
        return { background: 'rgba(251, 113, 131, 0.15)', color: 'var(--accent-coral)', border: '1px solid rgba(251, 113, 131, 0.3)' };
      case 'safe':
        return { background: 'var(--status-safe-bg)', color: 'var(--status-safe)', border: '1px solid var(--status-safe)' };
      case 'warning':
        return { background: 'var(--status-warning-bg)', color: 'var(--status-warning)', border: '1px solid var(--status-warning)' };
      case 'danger':
        return { background: 'var(--status-danger-bg)', color: 'var(--status-danger)', border: '1px solid var(--status-danger)' };
      case 'info':
        return { background: 'rgba(2, 132, 199, 0.15)', color: 'var(--status-info)', border: '1px solid var(--status-info)' };
      case 'cyan':
      default:
        return { background: 'var(--accent-cyan-glow)', color: 'var(--accent-cyan)', border: '1px solid rgba(6, 182, 212, 0.3)' };
    }
  };

  const getSizeStyle = (): React.CSSProperties => {
    return size === 'sm'
      ? { padding: '2px 6px', fontSize: '10px', height: '18px' }
      : { padding: '4px 10px', fontSize: '11px', height: '22px' };
  };

  return (
    <span
      className={`prism-badge ${className}`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '4px',
        fontWeight: 600,
        borderRadius: 'var(--radius-full)',
        whiteSpace: 'nowrap',
        userSelect: 'none',
        ...getColorStyle(),
        ...getSizeStyle(),
        ...style,
      }}
      {...props}
    >
      {children}
    </span>
  );
};
