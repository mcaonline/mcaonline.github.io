

interface ConfirmDialogProps {
    isOpen: boolean;
    title: string;
    message: string;
    onReset: () => void;
    onConfirm: () => void;
    confirmLabel?: string;
    cancelLabel?: string;
    isAlert?: boolean;
}

export default function ConfirmDialog({
    isOpen,
    title,
    message,
    onReset,
    onConfirm,
    confirmLabel = "OK",
    cancelLabel = "Cancel",
    isAlert = false
}: ConfirmDialogProps) {
    if (!isOpen) return null;

    return (
        <div className="modal-overlay">
            <div className="modal-content glass-pane">
                <h3 style={{ marginTop: 0, marginBottom: "12px", color: "var(--accent-primary)" }}>{title}</h3>
                <p style={{ marginBottom: "24px", fontSize: "0.95rem", lineHeight: 1.5 }}>{message}</p>
                <div style={{ display: "flex", justifyContent: "flex-end", gap: "12px" }}>
                    {!isAlert && (
                        <button className="secondary" onClick={onReset} style={{ boxShadow: "none" }}>
                            {cancelLabel}
                        </button>
                    )}
                    <button onClick={onConfirm} style={{ minWidth: "80px" }}>
                        {confirmLabel}
                    </button>
                </div>
            </div>
        </div>
    );
}
