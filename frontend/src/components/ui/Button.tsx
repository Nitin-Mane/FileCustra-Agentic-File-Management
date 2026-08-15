import React from 'react';
import { Loader2 } from 'lucide-react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  leftIcon,
  rightIcon,
  className = '',
  disabled,
  ...props
}) => {
  const getVariantStyle = (): React.CSSProperties => {
    switch (variant) {
      case 'primary':
        return {
          background: 'linear-gradient(135deg, var(--accent-cyan), var(--accent-violet))',
          color: '#ffffff',
          border: 'none',
          boxShadow: 'var(--shadow-glow)',
        };
      case 'secondary':
        return {
          background: 'var(--bg-tertiary)',
          color: 'var(--text-primary)',
          border: '1px solid var(--border-subtle)',
        };
      case 'danger':
        return {
          background: 'var(--status-danger-bg)',
          color: 'var(--status-danger)',
          border: '1px solid var(--status-danger)',
        };
      case 'outline':
        return {
          background: 'transparent',
          color: 'var(--accent-aqua)',
          border: '1px solid var(--border-active)',
        };
      case 'ghost':
      default:
        return {
          background: 'transparent',
          color: 'var(--text-secondary)',
          border: 'none',
        };
    }
  };

  const getSizeStyle = (): React.CSSProperties => {
    switch (size) {
      case 'sm':
        return { padding: '4px 10px', fontSize: '11px', height: '30px' };
      case 'lg':
        return { padding: '10px 22px', fontSize: '14px', height: '44px' };
      case 'md':
      default:
        return { padding: '7px 16px', fontSize: '12px', height: '36px' };
    }
  };

  return (
    <button
      className={`prism-btn ${className}`}
      disabled={disabled || isLoading}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '6px',
        fontWeight: 600,
        borderRadius: 'var(--radius-sm)',
        cursor: disabled || isLoading ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.6 : 1,
        transition: 'all var(--transition-fast)',
        userSelect: 'none',
        ...getVariantStyle(),
        ...getSizeStyle(),
      }}
      {...props}
    >
      {isLoading ? (
        <Loader2 className="animate-spin" size={size === 'sm' ? 12 : 16} />
      ) : (
        leftIcon
      )}
      <span>{children}</span>
      {!isLoading && rightIcon}
    </button>
  );
};
