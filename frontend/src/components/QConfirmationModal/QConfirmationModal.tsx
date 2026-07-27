import { type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import QModal from '@components/QModal';
import Qbutton from '@components/Qbutton';

import CheckIcon from '@assets/icons/check_icon.svg?react';

import './QConfirmationModal.css';

interface QConfirmationModalProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title?: ReactNode;
  subtitle?: ReactNode;
  /** Optional illustrative icon shown centered above the subtitle. */
  confirmText?: string;
  /** Cancel button label. Defaults to `shared.cancel`. */
  cancelText?: string;
  /** Controlled loading state for the confirm button. */
  isConfirming?: boolean;
  /** Renders the confirm button with a destructive (danger) style. */
  destructive?: boolean;
  /** Forwarded to QModal — centers the title within the header. */
  centerTitle?: boolean;
  /** Forwarded to QModal — overrides the title colour. */
  titleColor?: string;
  /** Optional extra class on the root modal element. */
  className?: string;
}

function QConfirmationModal({
  open,
  onClose,
  onConfirm,
  title,
  subtitle,
  confirmText,
  cancelText,
  isConfirming = false,
  destructive = false,
  centerTitle = false,
  titleColor,
  className = '',
}: QConfirmationModalProps) {
  const { t } = useTranslation();

  const confirmClass = [
    'qconfirmation-modal__confirm',
    'uppercase',
    destructive ? 'qconfirmation-modal__confirm--danger' : '',
  ]
    .filter(Boolean)
    .join(' ');

  const modalClass = ['qconfirmation-modal', className].filter(Boolean).join(' ');

  return (
    <QModal
      open={open}
      onClose={onClose}
      title={title}
      showClose
      closeOnOverlayClick={false}
      closeOnEscape={!isConfirming}
      centerTitle={centerTitle}
      titleColor={titleColor}
      className={modalClass}
    >
      <div className="qconfirmation-modal__content">
        <span className="qconfirmation-modal__icon" aria-hidden="true">
          <CheckIcon />
        </span>
        

        {subtitle !== undefined && (
          <p className="qconfirmation-modal__subtitle">{subtitle}</p>
        )}

        <footer className="qconfirmation-modal__footer">
          <Qbutton
            type="button"
            className="qconfirmation-modal__cancel uppercase"
            onClick={onClose}
            text={cancelText ?? t('shared.cancel')}
            disable={isConfirming}
          />
          <Qbutton
            type="button"
            className={confirmClass}
            onClick={onConfirm}
            text={confirmText ?? t('shared.confirm')}
            loading={isConfirming}
            disable={isConfirming}
          />
        </footer>
      </div>
    </QModal>
  );
}

export default QConfirmationModal;
