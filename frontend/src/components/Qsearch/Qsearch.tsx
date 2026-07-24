import { type InputHTMLAttributes } from 'react';
import './Qsearch.css';

interface QsearchProps
  extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> {
  placeholder: string;
}

function Qsearch({ placeholder, className = '', ...rest }: QsearchProps) {
  const classes = ['input', 'qsearch__field', className]
    .filter(Boolean)
    .join(' ');

  return (
    <div className="qsearch">
      <input
        type="search"
        className={classes}
        placeholder={placeholder}
        {...rest}
      />
      <svg
        className="qsearch__icon"
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
      >
        <circle cx="11" cy="11" r="7" stroke="currentColor" strokeWidth="1.5" />
        <line x1="16" y1="16" x2="20" y2="20" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      </svg>
    </div>
  );
}

export default Qsearch;
