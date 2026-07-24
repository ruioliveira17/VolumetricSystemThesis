import { useEffect, type ReactNode } from 'react';
import { createPortal } from 'react-dom';
import CloseIcon from '@assets/icons/close.svg?react';
import './QModal.css';

interface QModalProps {
  open: boolean;
  onClose: () => void;
  title?: ReactNode;
  children: ReactNode;
  showClose?: boolean;
  closeOnOverlayClick?: boolean;
  closeOnEscape?: boolean;
  /** When true, the title is centered horizontally within the modal and the close button is anchored to the right edge. */
  centerTitle?: boolean;
  /**
   * Overrides the title colour. Accepts any CSS color value — prefer a design
   * token (e.g. `var(--color-accent-success)`) over a raw hex literal.
   */
  titleColor?: string;
  className?: string;
}

function QModal({
  open,
  onClose,
  title,
  children,
  showClose = true,
  closeOnOverlayClick = true,
  closeOnEscape = true,
  centerTitle = false,
  titleColor,
  className = '',
}: QModalProps) {
  useEffect(() => {
    if (!open || !closeOnEscape) return;

    function handleKey(event: KeyboardEvent) {
      if (event.key === 'Escape') onClose();
    }

    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [open, onClose, closeOnEscape]);

  useEffect(() => {
    if (!open) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [open]);

  if (!open) return null;

  const modalClasses = ['qmodal', className].filter(Boolean).join(' ');
  const headerClasses = [
    'qmodal__header',
    centerTitle ? 'qmodal__header--center-title' : '',
  ]
    .filter(Boolean)
    .join(' ');

  return createPortal(
    <div
      className="qmodal-overlay"
      onClick={closeOnOverlayClick ? onClose : undefined}
    >
      <div
        className={modalClasses}
        role="dialog"
        aria-modal="true"
        aria-labelledby={title ? 'qmodal-title' : undefined}
        onClick={(event) => event.stopPropagation()}
      >
        {(title || showClose) && (
          <header className={headerClasses}>
            {title && (
              <h2
                id="qmodal-title"
                className="qmodal__title uppercase"
                style={titleColor ? { color: titleColor } : undefined}
              >
                {title}
              </h2>
            )}
            {showClose && (
              <button
                type="button"
                className="qmodal__close"
                onClick={onClose}
                aria-label="Close"
              >
               <CloseIcon />
              </button>
            )}
          </header>
        )}
        <div className="qmodal__body">{children}</div>
      </div>
    </div>,
    document.body,
  );
}

export default QModal;
