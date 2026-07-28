import { Toaster, toast, type ExternalToast } from 'sonner';
import DoneIcon from '@assets/icons/check_icon.svg?react';

import './QToast.css';
import { createPortal } from 'react-dom';

/** Dismiss action shown on every toast ("FECHAR"). */
const CLOSE_ACTION = { label: 'CLOSE', onClick: () => {} };

/**
 * App-wide toast container. Mount once near the app root.
 * Styling is fully owned by QToast.css (sonner runs unstyled).
 */
export function QToaster() {
  return createPortal(
    <Toaster
      position="bottom-center"
      offset={24}
      gap={12}
      // Keep toasts above modals (QModal overlay is z-index 1000)
      style={{ zIndex: 2000 }}
      toastOptions={{
        unstyled: true,
        classNames: {
          toast: 'qtoast',
          title: 'qtoast__title',
          icon: 'qtoast__icon',
          cancelButton: 'qtoast__close',
        },
      }}
    />,
    document.body
  );
}

/**
 * Toast helpers matching the Qilo design.
 * - success: green background with a check icon
 * - error: red background, no icon
 */
export const notify = {
  success: (message: string, options?: ExternalToast) =>
    toast.success(message, {
      icon: <DoneIcon className="qtoast__check" aria-hidden="true" />,
      cancel: CLOSE_ACTION,
      ...options,
    }),
  error: (message: string, options?: ExternalToast) =>
    toast.error(message, {
      icon: null,
      cancel: CLOSE_ACTION,
      ...options,
    }),
};

export { toast };
