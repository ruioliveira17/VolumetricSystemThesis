import { useEffect, useId, useRef, useState, type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import ArrowDropDown from '@assets/icons/arrow_drop_down_24dp.svg?react';
import './Qselect.css';

export interface QselectOption<T extends string = string> {
  value: T;
  label: string;
}

interface QselectProps<T extends string = string> {
  label: string;
  value: T;
  options: QselectOption<T>[];
  onChange: (value: T) => void;
  placeholder?: string;
  className?: string;
  disabled?: boolean;
  /** Optional leading icon shown at the left of the field (e.g. an SVG element). */
  icon?: ReactNode;
}

function Qselect<T extends string = string>({
  label,
  value,
  options,
  onChange,
  placeholder,
  className = '',
  disabled = false,
  icon,
}: QselectProps<T>) {
  const { t } = useTranslation();
  const reactId = useId();
  const listboxId = `${reactId}-listbox`;
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;

    function handleClickOutside(event: MouseEvent) {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    }

    function handleEscape(event: KeyboardEvent) {
      if (event.key === 'Escape') setOpen(false);
    }

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleEscape);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [open]);

  const selected = options.find((option) => option.value === value);
  const placeholderText = placeholder ?? t('shared.select');
  const showPlaceholder = open || !selected;
  const displayLabel = showPlaceholder ? placeholderText : selected!.label;

  const panelClasses = [
    'qselect__panel',
    open ? 'qselect__panel--open' : '',
  ]
    .filter(Boolean)
    .join(' ');

  const fieldClasses = [
    'input',
    'qselect__field',
    open ? 'qselect__field--open' : '',
    className,
  ]
    .filter(Boolean)
    .join(' ');

  const valueClasses = [
    'qselect__value',
    showPlaceholder ? 'qselect__value--placeholder' : '',
  ]
    .filter(Boolean)
    .join(' ');

  const rootClasses = ['qselect', icon ? 'qselect--with-icon' : '']
    .filter(Boolean)
    .join(' ');

  function handleSelect(nextValue: T) {
    onChange(nextValue);
    setOpen(false);
  }

  return (
    <div className={rootClasses} ref={rootRef}>
      <div className={panelClasses}>
        <button
          type="button"
          className={fieldClasses}
          onClick={() => !disabled && setOpen((prev) => !prev)}
          disabled={disabled}
          aria-haspopup="listbox"
          aria-expanded={open}
          aria-controls={listboxId}
        >
          {icon && (
            <span className="qselect__icon" aria-hidden="true">
              {icon}
            </span>
          )}
          <span className={valueClasses}>{displayLabel}</span>
          <ArrowDropDown className='qselect__chevron' />
        </button>

        <label className="qselect__label">{label}</label>

        <ul
          id={listboxId}
          className={
            open ? 'qselect__list qselect__list--open' : 'qselect__list'
          }
          role="listbox"
          aria-label={label}
          aria-hidden={!open}
        >
          {options.map((option) => {
            const isSelected = option.value === value;
            const optionClasses = [
              'qselect__option',
              isSelected ? 'qselect__option--selected' : '',
            ]
              .filter(Boolean)
              .join(' ');

            return (
              <li
                key={option.value}
                role="option"
                aria-selected={isSelected}
                className={optionClasses}
                onClick={() => handleSelect(option.value)}
              >
                <span className="qselect__option-label">{option.label}</span>
                {isSelected && (
                  <svg
                    className="qselect__option-check"
                    viewBox="0 0 16 16"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                    aria-hidden="true"
                  >
                    <path
                      d="M3 8.5 L6.5 12 L13 4.5"
                      stroke="currentColor"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                )}
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}

export default Qselect;
