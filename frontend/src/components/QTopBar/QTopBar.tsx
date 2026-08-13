import {
  useState,
  type CSSProperties,
  type MouseEvent,
  type ReactNode,
} from 'react';
import './QTopBar.css';

/**
 * A nav item. Rendered as an <a> by default; pass `renderLink` on the bar to
 * plug in a router link (NavLink, Next <Link>, …) without this component
 * depending on a router.
 */
export interface QTopBarNavItem {
  key: string;
  label: ReactNode;
  href?: string;
  /** Marks the item as the current page (dot + bold styling). */
  active?: boolean;
  order?: number;
  onClick?: (event: MouseEvent<HTMLAnchorElement>) => void;
}

/** An icon button in the right-hand actions cluster. */
export interface QTopBarAction {
  key: string;
  /** Any node — an SVG component instance, an <img>, a glyph. */
  icon?: ReactNode;
  /** aria-label for the button (icons carry no accessible name). */
  label?: string;
  active?: boolean;
  onClick?: (event: MouseEvent<HTMLButtonElement>) => void;
  /**
   * Escape hatch: render this node instead of the default button. Use it for
   * actions that own their own trigger (a popover, a menu, a dropdown).
   */
  render?: ReactNode;
}

export interface QTopBarProps {
  primaryNav?: QTopBarNavItem[];
  /** Nav links revealed by the toggle, sliding open from the right. */
  collapsibleNav?: QTopBarNavItem[];
  /** Always-visible icon buttons. */
  actions?: QTopBarAction[];
  /** Icon buttons revealed by the toggle, in their own sliding drawer. */
  collapsibleActions?: QTopBarAction[];
  /**
   * Width the collapsible actions drawer opens to. Defaults to 36px per
   * action — override when the actions aren't standard icon buttons.
   */
  collapsibleActionsWidth?: string;
  /** Hide the toggle button (e.g. when there is nothing collapsible). */
  showToggle?: boolean;
  /** Uncontrolled initial state. Ignored when `expanded` is passed. */
  defaultExpanded?: boolean;
  /** Controlled state — pair with `onExpandedChange`. */
  expanded?: boolean;
  onExpandedChange?: (expanded: boolean) => void;
  /** Swap the anchor for a router link. Receives the item plus bar-owned props. */
  expandLabel?: string;
  collapseLabel?: string;
  navLabel?: string;
  className?: string;
}

const ACTION_WIDTH = 46;

function QTopBar({
  primaryNav = [],
  collapsibleNav = [],
  actions = [],
  collapsibleActions = [],
  collapsibleActionsWidth,
  showToggle = true,
  defaultExpanded = true,
  expanded,
  onExpandedChange,
  expandLabel = 'Expand menu',
  collapseLabel = 'Collapse menu',
  navLabel = 'Main navigation',
  className = '',
}: QTopBarProps) {
  const [uncontrolled, setUncontrolled] = useState(defaultExpanded);
  const isControlled = expanded !== undefined;
  const isExpanded = isControlled ? expanded : uncontrolled;

  const toggle = () => {
    const next = !isExpanded;
    if (!isControlled) setUncontrolled(next);
    onExpandedChange?.(next);
  };

  const renderNavLink = (item: QTopBarNavItem) => {
    const linkClass = item.active
      ? 'qtopbar__nav-link qtopbar__nav-link--active'
      : 'qtopbar__nav-link';

    return (
      <a
        key={item.key}
        href={item.href}
        className={linkClass}
        aria-current={item.active ? 'page' : undefined}
        onClick={item.onClick}
      >
        {item.label}
      </a>
    );
  };

  const renderAction = (action: QTopBarAction) => {
    if (action.render) return <span key={action.key}>{action.render}</span>;

    return (
      <button
        key={action.key}
        type="button"
        className={`qtopbar__action${action.active ? ' qtopbar__action--active' : ''}`}
        aria-label={action.label}
        aria-current={action.active ? 'page' : undefined}
        onClick={(e) => action.onClick?.(e)}
      >
        {action.icon}
      </button>
    );
  };

  const hasNav = primaryNav.length > 0 || collapsibleNav.length > 0;

  const orderedNav = [...primaryNav, ...collapsibleNav].sort(
    (a, b) => (a.order ?? 0) - (b.order ?? 0)
  );

  const drawerStyle = {
    '--qtopbar-collapsible-actions-width':
      collapsibleActionsWidth ??
      `${Math.max(collapsibleActions.length, 1) * ACTION_WIDTH}px`,
  } as CSSProperties;

  return (
    <header className={`qtopbar ${className}`.trim()}>
      <div className="qtopbar__left">
      </div>

      <div className="qtopbar__right">
        {hasNav && (
          <nav className="qtopbar__nav" aria-label={navLabel}>
            {orderedNav.map((item) => {
              if (item.active) {
                  return renderNavLink(item);
              }

              return (
                  <div
                      key={item.key}
                      className={`qtopbar__nav-collapsible${
                          isExpanded ? ' qtopbar__nav-collapsible--open' : ''
                      }`}
                      aria-hidden={!isExpanded}
                  >
                      <div className="qtopbar__nav-collapsible-inner">
                          {renderNavLink(item)}
                      </div>
                  </div>
              );
            })}
          </nav>
        )}

        <div className="qtopbar__actions">
          {collapsibleActions.length > 0 && (
            <div
              className={`qtopbar__actions-collapsible${
                isExpanded ? ' qtopbar__actions-collapsible--open' : ''
              }`}
              style={drawerStyle}
              aria-hidden={!isExpanded}
            >
              {collapsibleActions.map(renderAction)}
            </div>
          )}

          {actions.map(renderAction)}

          {showToggle && (
            <button
              type="button"
              className={`qtopbar__action qtopbar__toggle${
                isExpanded ? ' qtopbar__toggle--open' : ''
              }`}
              aria-label={isExpanded ? collapseLabel : expandLabel}
              aria-expanded={isExpanded}
              onClick={toggle}
            >
              {/* The arrow is painted first so the three lines sit on top of it
                  as it slides behind them. */}
              <svg
                viewBox="0 0 24 24"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                aria-hidden="true"
              >
                <g className="qtopbar__toggle-arrow">
                  <polyline
                    points="20,9 17,12 20,15"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="square"
                    strokeLinejoin="miter"
                    fill="none"
                  />
                </g>
                <line
                  className="qtopbar__toggle-line--first"
                  x1="4"
                  y1="7"
                  x2="16"
                  y2="7"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="square"
                />
                <line
                  className="qtopbar__toggle-line--middle"
                  x1="4"
                  y1="12"
                  x2="12"
                  y2="12"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="square"
                />
                <line
                  className="qtopbar__toggle-line--last"
                  x1="4"
                  y1="17"
                  x2="16"
                  y2="17"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="square"
                />
              </svg>
            </button>
          )}
        </div>
      </div>
    </header>
  );
}

export default QTopBar;
