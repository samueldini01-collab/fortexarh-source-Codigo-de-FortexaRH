import { useEffect, useRef, useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Camera, RefreshCw, X as XIcon, SkipForward } from "lucide-react";

/**
 * SelfieCaptureDialog
 * Opens the device camera (front-facing preferred), lets the employee take a photo,
 * and returns a base64-encoded JPEG via onCapture.
 *
 * Props:
 *  - open (bool)
 *  - onCancel()
 *  - onSkip()             — proceed without a selfie
 *  - onCapture(base64)    — data URL prefix stripped: "data:image/jpeg;base64,..."
 *  - title (optional)
 */
export function SelfieCaptureDialog({ open, onCancel, onSkip, onCapture, title = "Toma tu selfie para ponchar" }) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const [error, setError] = useState(null);
  const [preview, setPreview] = useState(null); // base64 preview

  useEffect(() => {
    if (!open) {
      // Stop any active stream when dialog closes
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
        streamRef.current = null;
      }
      setPreview(null);
      setError(null);
      return;
    }

    let cancelled = false;
    (async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: "user", width: { ideal: 640 }, height: { ideal: 480 } },
          audio: false,
        });
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      } catch (e) {
        setError(
          e?.name === "NotAllowedError"
            ? "Permiso de cámara denegado. Habilita el acceso a la cámara para tomar tu selfie."
            : "No pudimos acceder a la cámara del dispositivo."
        );
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [open]);

  const handleCapture = () => {
    if (!videoRef.current || !canvasRef.current) return;
    const video = videoRef.current;
    const canvas = canvasRef.current;
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const dataUrl = canvas.toDataURL("image/jpeg", 0.75);
    setPreview(dataUrl);
  };

  const handleRetake = () => setPreview(null);

  const handleConfirm = () => {
    if (!preview) return;
    // Strip the data URL prefix; backend stores the raw base64
    const base64 = preview.replace(/^data:image\/\w+;base64,/, "");
    onCapture(base64);
  };

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onCancel()}>
      <DialogContent className="max-w-md" data-testid="selfie-capture-dialog">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
        </DialogHeader>

        {error ? (
          <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded p-3">
            {error}
          </div>
        ) : (
          <div className="relative bg-slate-900 rounded overflow-hidden aspect-video">
            {!preview ? (
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="w-full h-full object-cover"
                data-testid="selfie-video-preview"
              />
            ) : (
              <img
                src={preview}
                alt="Selfie preview"
                className="w-full h-full object-cover"
                data-testid="selfie-preview-image"
              />
            )}
            <canvas ref={canvasRef} className="hidden" />
          </div>
        )}

        <DialogFooter className="gap-2 flex-wrap">
          <Button
            variant="outline"
            size="sm"
            onClick={onCancel}
            data-testid="selfie-cancel-btn"
          >
            <XIcon className="w-4 h-4 mr-1" /> Cancelar
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={onSkip}
            data-testid="selfie-skip-btn"
          >
            <SkipForward className="w-4 h-4 mr-1" /> Omitir
          </Button>
          {!preview ? (
            <Button
              size="sm"
              onClick={handleCapture}
              disabled={!!error}
              data-testid="selfie-take-btn"
            >
              <Camera className="w-4 h-4 mr-1" /> Tomar foto
            </Button>
          ) : (
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={handleRetake}
                data-testid="selfie-retake-btn"
              >
                <RefreshCw className="w-4 h-4 mr-1" /> Repetir
              </Button>
              <Button size="sm" onClick={handleConfirm} data-testid="selfie-confirm-btn">
                Usar esta foto
              </Button>
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
