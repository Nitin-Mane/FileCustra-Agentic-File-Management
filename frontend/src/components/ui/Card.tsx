import React from 'react';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'glass' | 'solid' | 'bordered';
  hoverable?: boolean;
  glowing?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  variant = 'glass',
  hoverable = false,
  glowing = false,
  className = '',
  style = {},
  ...props
}) => {
  const getVariantStyle = (): React.CSSProperties => {
    switch (variant) {
      case 'solid':
        return {
          background: 'var(--bg-tertiary)',
          border: '1px solid var(--border-subtle)',
        };
      case 'bordered':
        return {
          background: 'rgba(17, 24, 39, 0.4)',
          border: '1px solid var(--border-active)',
        };
      case 'glass':
      default:
        return {
          background: 'var(--bg-glass)',
          backdropFilter: 'blur(12px)',
          border: '1px solid var(--border-subtle)',
        };
    }
  };

  return (
    <div
      className={`prism-card ${hoverable ? 'hoverable' : ''} ${className}`}
      style={{
        borderRadius: 'var(--radius-md)',
        padding: '16px',
        boxShadow: glowing ? 'var(--shadow-glow)' : 'var(--shadow-card)',
        transition: 'all var(--transition-fast)',
        ...getVariantStyle(),
        ...style,
      }}
      {...props}
    >
      {children}
    </div>
  );
};
