import { Icon } from "./Icon";

export type ToastData = {
  id: number;
  title: string;
  message: string;
};

export function Toast({
  toast,
  onClose,
}: {
  toast: ToastData;
  onClose: () => void;
}) {
  return (
    <div className="avis-toast" role="status">
      <div className="toast-icon">
        <Icon type="check" size={15} />
      </div>
      <div>
        <strong>{toast.title}</strong>
        <span>{toast.message}</span>
      </div>
      <button className="icon-button small" onClick={onClose} aria-label="Dismiss">
        <Icon type="x" size={14} />
      </button>
    </div>
  );
}