import { useState } from "react";
import axios from "axios";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Camera, ImageOff, ZoomIn, X } from "lucide-react";

const API = process.env.REACT_APP_BACKEND_URL ? `${process.env.REACT_APP_BACKEND_URL}/api` : "/api";

/**
 * AttendanceSelfieCell
 * Renders small "In" / "Out" selfie thumbnails inside an attendance row.
 * Fetches images from /api/attendance/selfies/{selfie_id} with the admin's token.
 * Clicking a thumbnail opens a full-size preview.
 *
 * Props:
 *  - checkInSelfieId?: string
 *  - checkOutSelfieId?: string
 *  - authHeaders: object   — Authorization header for the fetch
 */
export function AttendanceSelfieCell({ checkInSelfieId, checkOutSelfieId, authHeaders }) {
  if (!checkInSelfieId && !checkOutSelfieId) {
    return (
      <div
        className="text-slate-400 text-xs flex items-center gap-1"
        data-testid="attendance-selfie-cell-empty"
      >
        <ImageOff className="w-3 h-3" /> —
      </div>
    );
  }

  return (
    <div className="flex items-center gap-1" data-testid="attendance-selfie-cell">
      {checkInSelfieId && (
        <SelfieThumb selfieId={checkInSelfieId} label="Entrada" authHeaders={authHeaders} />
      )}
      {checkOutSelfieId && (
        <SelfieThumb selfieId={checkOutSelfieId} label="Salida" authHeaders={authHeaders} />
      )}
    </div>
  );
}

function SelfieThumb({ selfieId, label, authHeaders }) {
  const [objectUrl, setObjectUrl] = useState(null);
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(false);
  const [openPreview, setOpenPreview] = useState(false);

  const loadImage = async () => {
    if (objectUrl || loading) return;
    setLoading(true);
    try {
      const res = await axios.get(`${API}/attendance/selfies/${selfieId}`, {
        headers: authHeaders,
        responseType: "blob",
      });
      const url = URL.createObjectURL(res.data);
      setObjectUrl(url);
    } catch (e) {
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  // Lazy-load: fetch on first hover/focus so table doesn't request 100+ images upfront
  const handleEnter = () => {
    if (!objectUrl && !error && !loading) loadImage();
  };

  const handleOpen = async () => {
    if (!objectUrl) await loadImage();
    setOpenPreview(true);
  };

  return (
    <>
      <button
        type="button"
        onMouseEnter={handleEnter}
        onFocus={handleEnter}
        onClick={handleOpen}
        title={`${label} — clic para ampliar`}
        className="relative group rounded overflow-hidden border border-slate-200 hover:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-400"
        style={{ width: 32, height: 32 }}
        data-testid={`selfie-thumb-${selfieId}`}
      >
        {objectUrl ? (
          <img src={objectUrl} alt={label} className="w-full h-full object-cover" />
        ) : (
          <div className="w-full h-full bg-slate-100 flex items-center justify-center">
            <Camera className="w-3 h-3 text-slate-500" />
          </div>
        )}
        <span className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition flex items-center justify-center">
          <ZoomIn className="w-3 h-3 text-white opacity-0 group-hover:opacity-100" />
        </span>
      </button>

      <Dialog open={openPreview} onOpenChange={setOpenPreview}>
        <DialogContent className="max-w-lg" data-testid="selfie-preview-dialog">
          <DialogHeader>
            <DialogTitle>Selfie — {label}</DialogTitle>
          </DialogHeader>
          {error ? (
            <div className="text-sm text-red-600 bg-red-50 p-3 rounded">
              No se pudo cargar la selfie.
            </div>
          ) : objectUrl ? (
            <img
              src={objectUrl}
              alt={label}
              className="w-full rounded"
              data-testid="selfie-preview-image-full"
            />
          ) : (
            <div className="text-sm text-slate-500 p-6 text-center">Cargando…</div>
          )}
          <div className="flex justify-end">
            <Button variant="outline" size="sm" onClick={() => setOpenPreview(false)}>
              <X className="w-4 h-4 mr-1" /> Cerrar
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
