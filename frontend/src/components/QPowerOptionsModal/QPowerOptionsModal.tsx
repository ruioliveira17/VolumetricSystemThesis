import { type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import QModal from '@components/QModal';
import Qbutton from '@components/Qbutton';

import PowerIcon from '@assets/icons/power.svg?react';

import './QPowerOptionsModal.css';

interface QPowerOptionsModalProps {
  open: boolean;
  onClose: () => void;
  
  option1Text: string;
  option2Text: string;

  onOption1: () => void;
  onOption2: () => void;

  title?: ReactNode;
  subtitle?: ReactNode;

  /** Renders option 1 with a destructive (danger) style. */
  option1Destructive?: boolean;

  /** Renders option 2 with a destructive (danger) style. */
  option2Destructive?: boolean;

  /** Forwarded to QModal — centers the title within the header. */
  centerTitle?: boolean;

  /** Forwarded to QModal — overrides the title colour. */
  titleColor?: string;

  /** Optional extra class on the root modal element. */
  className?: string;

  container?: Element | null;
}

function QPowerOptionsModal({
  open,
  onClose,
  onOption1,
  onOption2,
  option1Text,
  option2Text,
  title,
  subtitle,
  option1Destructive = false,
  option2Destructive = false,
  centerTitle = false,
  titleColor,
  className = '',
  container,
}: QPowerOptionsModalProps) {
  const { t } = useTranslation();

  const option1Class = [
    'qpower_options-modal__option',
    'uppercase',
    option1Destructive ? 'qpower_options-modal__option--danger' : '',
  ]
    .filter(Boolean)
    .join(' ');

  const option2Class = [
    'qpower_options-modal__option',
    'uppercase',
    option2Destructive ? 'qpower_options-modal__option--danger' : '',
  ]
    .filter(Boolean)
    .join(' ');

  const modalClass = ['qpower_options-modal', className]
    .filter(Boolean)
    .join(' ');

  return (
    <QModal
      open={open}
      onClose={onClose}
      title={title}
      showClose
      closeOnOverlayClick={false}
      closeOnEscape
      centerTitle={centerTitle}
      titleColor={titleColor}
      className={modalClass}
      container={container}
    >
      <div className="qpower_options-modal__content">
        <span className="qpower_options-modal__icon" aria-hidden="true">
          <PowerIcon />
        </span>
        

        {subtitle !== undefined && (
          <p className="qpower_options-modal__subtitle">{subtitle}</p>
        )}

        <footer className="qpower_options-modal__footer">
          <Qbutton
            type="button"
            className={option1Class}
            onClick={onOption1}
            text={option1Text}
          />
          <Qbutton
            type="button"
            className={option2Class}
            onClick={onOption2}
            text={option2Text}
          />
        </footer>
      </div>
    </QModal>
  );
}

export default QPowerOptionsModal;
