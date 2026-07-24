import type { ButtonHTMLAttributes, ComponentType, ReactNode } from 'react';
import './Qbutton.css';

type IconProp = ReactNode | ComponentType<{ className?: string }>;

interface QbuttonProps
  extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'disabled'> {
  text: string;
  disable?: boolean;
  loading?: boolean;
  icon?: IconProp;
}

function renderIcon(icon: IconProp): ReactNode {
  if (typeof icon === 'function') {
    const Icon = icon;
    return <Icon className="qbutton__icon-svg" />;
  }
  return icon;
}

function Qbutton({
  text,
  disable = false,
  loading = false,
  icon,
  className = '',
  ...rest
}: QbuttonProps) {
  const isDisabled = disable || loading;

  const classes = [
    'button',
    'qbutton',
    icon ? 'qbutton--with-icon' : '',
    loading ? 'qbutton--loading' : '',
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <button className={classes} disabled={isDisabled} {...rest}>
      {loading ? (
        <span className="qbutton__spinner" aria-hidden="true" />
      ) : (
        icon && <span className="qbutton__icon">{renderIcon(icon)}</span>
      )}
      <span className="qbutton__text">{text}</span>
    </button>
  );
}

export default Qbutton;
