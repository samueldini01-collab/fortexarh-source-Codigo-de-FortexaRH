import { useState, useEffect, useRef, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import axios from "axios";
import { useAuth } from "@/App";
import { 
  MapPin, 
  Clock, 
  Camera, 
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  LogIn,
  LogOut,
  RefreshCw,
  Navigation,
  History,
  Building2,
  Wifi,
  WifiOff,
  ChevronRight
} from "lucide-react";

const API = process.env.REACT_APP_BACKEND_URL + "/api";

export default function GeoAttendancePage() {
  const { t } = useTranslation();
  const { getAuthHeaders, user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [marking, setMarking] = useState(false);
  const [location, setLocation] = useState(null);
  const [locationError, setLocationError] = useState(null);
  const [todayMarks, setTodayMarks] = useState([]);
  const [myLocations, setMyLocations] = useState([]);
  const [nearestLocation, setNearestLocation] = useState(null);
  const [selfieData, setSelfieData] = useState(null);
  const [showCamera, setShowCamera] = useState(false);
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);

  // Check online status
  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Get current location
  const getCurrentLocation = useCallback(() => {
    setLocationError(null);
    
    if (!navigator.geolocation) {
      setLocationError(t("geoAttendance.mobile.locationErrors.notSupported"));
      return;
    }
    
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const loc = {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: position.coords.accuracy
        };
        setLocation(loc);
        
        // Find nearest location
        if (myLocations.length > 0) {
          let nearest = null;
          let minDistance = Infinity;
          
          myLocations.forEach(myLoc => {
            const distance = calculateDistance(
              loc.latitude, loc.longitude,
              myLoc.latitude, myLoc.longitude
            );
            if (distance < minDistance) {
              minDistance = distance;
              nearest = { ...myLoc, distance };
            }
          });
          
          setNearestLocation(nearest);
        }
      },
      (error) => {
        switch (error.code) {
          case error.PERMISSION_DENIED:
            setLocationError(t("geoAttendance.mobile.locationErrors.permissionDenied"));
            break;
          case error.POSITION_UNAVAILABLE:
            setLocationError(t("geoAttendance.mobile.locationErrors.positionUnavailable"));
            break;
          case error.TIMEOUT:
            setLocationError(t("geoAttendance.mobile.locationErrors.timeout"));
            break;
          default:
            setLocationError(t("geoAttendance.mobile.locationErrors.unknown"));
        }
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0
      }
    );
  }, [myLocations]);

  // Calculate distance between two points (Haversine formula)
  const calculateDistance = (lat1, lon1, lat2, lon2) => {
    const R = 6371000; // Earth's radius in meters
    const φ1 = lat1 * Math.PI / 180;
    const φ2 = lat2 * Math.PI / 180;
    const Δφ = (lat2 - lat1) * Math.PI / 180;
    const Δλ = (lon2 - lon1) * Math.PI / 180;

    const a = Math.sin(Δφ/2) * Math.sin(Δφ/2) +
              Math.cos(φ1) * Math.cos(φ2) *
              Math.sin(Δλ/2) * Math.sin(Δλ/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));

    return R * c;
  };

  // Fetch my locations and today's marks
  const fetchData = useCallback(async () => {
    if (!isOnline) return;
    
    setLoading(true);
    try {
      const [locationsRes, marksRes] = await Promise.all([
        axios.get(`${API}/geolocation-attendance/my-locations`, { headers: getAuthHeaders(), withCredentials: true }),
        axios.get(`${API}/geolocation-attendance/my-marks`, { headers: getAuthHeaders(), withCredentials: true })
      ]);
      
      setMyLocations(locationsRes.data);
      setTodayMarks(marksRes.data);
    } catch (error) {
      console.error("Error fetching data:", error);
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders, isOnline]);

  useEffect(() => {
    fetchData();
    getCurrentLocation();
    
    // Refresh location every 30 seconds
    const interval = setInterval(getCurrentLocation, 30000);
    return () => clearInterval(interval);
  }, [fetchData, getCurrentLocation]);

  // Camera functions
  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { facingMode: "user", width: 640, height: 480 } 
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setShowCamera(true);
    } catch (error) {
      toast.error(t("geoAttendance.messages.cameraAccessDenied"));
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
    }
    setShowCamera(false);
  };

  const takeSelfie = () => {
    if (videoRef.current && canvasRef.current) {
      const canvas = canvasRef.current;
      const video = videoRef.current;
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0);
      const dataUrl = canvas.toDataURL('image/jpeg', 0.7);
      setSelfieData(dataUrl);
      stopCamera();
    }
  };

  // Mark attendance
  const markAttendance = async (markType) => {
    if (!location) {
      toast.error(t("geoAttendance.messages.waitingForGps"));
      getCurrentLocation();
      return;
    }
    
    if (!isOnline) {
      toast.error(t("geoAttendance.messages.noInternet"));
      return;
    }
    
    setMarking(true);
    
    try {
      const response = await axios.post(
        `${API}/geolocation-attendance/mark`,
        {
          latitude: location.latitude,
          longitude: location.longitude,
          accuracy: location.accuracy,
          mark_type: markType,
          selfie_base64: selfieData,
          device_info: navigator.userAgent
        },
        { headers: getAuthHeaders(), withCredentials: true }
      );
      
      toast.success(response.data.message);
      
      if (!response.data.is_within_zone) {
        toast.warning(t("geoAttendance.messages.markOutsideZone"));
      }
      
      // Refresh data
      setSelfieData(null);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || t("geoAttendance.messages.errorMarkAttendance"));
    } finally {
      setMarking(false);
    }
  };

  // Check if already marked
  const hasMarkedEntry = todayMarks.some(m => m.mark_type === "entry");
  const hasMarkedExit = todayMarks.some(m => m.mark_type === "exit");
  
  // Format time
  const formatTime = (timestamp) => {
    if (!timestamp) return "";
    return new Date(timestamp).toLocaleTimeString('es-DO', { hour: '2-digit', minute: '2-digit' });
  };

  // Get status color
  const getStatusColor = (isWithinZone) => {
    return isWithinZone ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700";
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 text-white">
      {/* Header */}
      <div className="sticky top-0 z-50 bg-slate-900/95 backdrop-blur border-b border-slate-700 px-4 py-3">
        <div className="flex items-center justify-between max-w-lg mx-auto">
          <div className="flex items-center gap-2">
            <Building2 className="w-6 h-6 text-emerald-400" />
            <span className="font-bold text-lg">FortexaRH</span>
          </div>
          <div className="flex items-center gap-2">
            {isOnline ? (
              <Badge className="bg-emerald-500/20 text-emerald-300 border-emerald-500/50">
                <Wifi className="w-3 h-3 mr-1" />
                {t("geoAttendance.mobile.online")}
              </Badge>
            ) : (
              <Badge className="bg-red-500/20 text-red-300 border-red-500/50">
                <WifiOff className="w-3 h-3 mr-1" />
                {t("geoAttendance.mobile.offline")}
              </Badge>
            )}
          </div>
        </div>
      </div>

      <div className="max-w-lg mx-auto px-4 py-6 space-y-6">
        {/* Welcome Card */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="p-6">
            <div className="text-center">
              <p className="text-slate-400 text-sm">{t("geoAttendance.mobile.greeting.morning")}</p>
              <h1 className="text-2xl font-bold text-white mt-1">
                {user?.name || user?.email?.split('@')[0] || "Usuario"}
              </h1>
              <p className="text-slate-400 text-sm mt-2">
                {new Date().toLocaleDateString('es-DO', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Location Status */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center gap-2 text-white">
              <MapPin className="w-5 h-5 text-emerald-400" />
              {t("geoAttendance.mobile.currentLocation")}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {locationError ? (
              <div className="flex items-center gap-3 p-4 bg-red-500/20 rounded-lg border border-red-500/30">
                <XCircle className="w-6 h-6 text-red-400" />
                <div>
                  <p className="text-red-300 text-sm">{locationError}</p>
                  <Button 
                    variant="link" 
                    className="text-red-400 p-0 h-auto"
                    onClick={getCurrentLocation}
                  >
                    {t("geoAttendance.mobile.retry")}
                  </Button>
                </div>
              </div>
            ) : location ? (
              <>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-emerald-500/20 flex items-center justify-center">
                      <Navigation className="w-5 h-5 text-emerald-400" />
                    </div>
                    <div>
                      <p className="text-sm text-slate-400">{t("geoAttendance.mobile.gpsActive")}</p>
                      <p className="text-xs text-slate-500">{t("geoAttendance.mobile.accuracy")}: {Math.round(location.accuracy)}m</p>
                    </div>
                  </div>
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    onClick={getCurrentLocation}
                    className="text-slate-400"
                  >
                    <RefreshCw className="w-4 h-4" />
                  </Button>
                </div>
                
                {nearestLocation && (
                  <div className={`p-4 rounded-lg border ${
                    nearestLocation.distance <= nearestLocation.radius 
                      ? 'bg-emerald-500/10 border-emerald-500/30' 
                      : 'bg-amber-500/10 border-amber-500/30'
                  }`}>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-white">{nearestLocation.name}</p>
                        <p className="text-sm text-slate-400">{nearestLocation.address}</p>
                      </div>
                      {nearestLocation.distance <= nearestLocation.radius ? (
                        <Badge className="bg-emerald-500/20 text-emerald-300">
                          <CheckCircle className="w-3 h-3 mr-1" />
                          {t("geoAttendance.mobile.inside")}
                        </Badge>
                      ) : (
                        <Badge className="bg-amber-500/20 text-amber-300">
                          <AlertTriangle className="w-3 h-3 mr-1" />
                          {Math.round(nearestLocation.distance)}m
                        </Badge>
                      )}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="flex items-center gap-3 p-4 bg-slate-700/50 rounded-lg">
                <RefreshCw className="w-5 h-5 text-slate-400 animate-spin" />
                <p className="text-slate-400">{t("geoAttendance.mobile.gettingLocation")}</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Selfie Camera */}
        {showCamera && (
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center gap-2 text-white">
                <Camera className="w-5 h-5 text-blue-400" />
                {t("geoAttendance.mobile.selfieVerification")}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="relative rounded-lg overflow-hidden bg-black">
                <video 
                  ref={videoRef} 
                  autoPlay 
                  playsInline 
                  muted 
                  className="w-full"
                  style={{ transform: 'scaleX(-1)' }}
                />
              </div>
              <div className="flex gap-3">
                <Button 
                  onClick={takeSelfie} 
                  className="flex-1 bg-blue-600 hover:bg-blue-700"
                >
                  <Camera className="w-4 h-4 mr-2" />
                  {t("geoAttendance.mobile.takePhoto")}
                </Button>
                <Button 
                  onClick={stopCamera} 
                  variant="outline"
                  className="border-slate-600 text-slate-300"
                >
                  {t("geoAttendance.mobile.cancel")}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Selfie Preview */}
        {selfieData && !showCamera && (
          <Card className="bg-slate-800/50 border-slate-700">
            <CardContent className="p-4">
              <div className="flex items-center gap-4">
                <img 
                  src={selfieData} 
                  alt="Selfie" 
                  className="w-20 h-20 rounded-lg object-cover"
                  style={{ transform: 'scaleX(-1)' }}
                />
                <div className="flex-1">
                  <p className="text-emerald-400 flex items-center gap-2">
                    <CheckCircle className="w-4 h-4" />
                    {t("geoAttendance.mobile.photoCaptured")}
                  </p>
                  <Button 
                    variant="link" 
                    className="text-slate-400 p-0 h-auto"
                    onClick={() => setSelfieData(null)}
                  >
                    {t("geoAttendance.mobile.takeAnother")}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Canvas for capturing */}
        <canvas ref={canvasRef} className="hidden" />

        {/* Mark Buttons */}
        <div className="grid grid-cols-2 gap-4">
          <Button
            size="lg"
            className={`h-24 flex-col gap-2 ${
              hasMarkedEntry 
                ? 'bg-slate-700 text-slate-400 cursor-not-allowed' 
                : 'bg-emerald-600 hover:bg-emerald-700'
            }`}
            disabled={hasMarkedEntry || marking || !location}
            onClick={() => {
              if (!selfieData) {
                startCamera();
              } else {
                markAttendance("entry");
              }
            }}
          >
            <LogIn className="w-8 h-8" />
            <span className="font-semibold">
              {hasMarkedEntry ? t("geoAttendance.mobile.entryMarked") : (selfieData ? t("geoAttendance.mobile.confirmEntry") : t("geoAttendance.mobile.markEntry"))}
            </span>
          </Button>
          
          <Button
            size="lg"
            className={`h-24 flex-col gap-2 ${
              hasMarkedExit || !hasMarkedEntry
                ? 'bg-slate-700 text-slate-400 cursor-not-allowed' 
                : 'bg-rose-600 hover:bg-rose-700'
            }`}
            disabled={hasMarkedExit || !hasMarkedEntry || marking || !location}
            onClick={() => {
              if (!selfieData) {
                startCamera();
              } else {
                markAttendance("exit");
              }
            }}
          >
            <LogOut className="w-8 h-8" />
            <span className="font-semibold">
              {hasMarkedExit ? t("geoAttendance.mobile.exitMarked") : (selfieData ? t("geoAttendance.mobile.confirmExit") : t("geoAttendance.mobile.markExit"))}
            </span>
          </Button>
        </div>

        {/* Loading indicator */}
        {marking && (
          <div className="flex items-center justify-center gap-3 p-4 bg-slate-700/50 rounded-lg">
            <RefreshCw className="w-5 h-5 text-emerald-400 animate-spin" />
            <p className="text-slate-300">{t("geoAttendance.mobile.registeringMark")}</p>
          </div>
        )}

        {/* Today's Marks */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center gap-2 text-white">
              <History className="w-5 h-5 text-purple-400" />
              {t("geoAttendance.mobile.todayMarks")}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {todayMarks.length === 0 ? (
              <p className="text-slate-400 text-center py-6">
                {t("geoAttendance.messages.noMarksToday")}
              </p>
            ) : (
              <div className="space-y-3">
                {todayMarks.map((mark, idx) => (
                  <div 
                    key={idx} 
                    className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                        mark.mark_type === 'entry' ? 'bg-emerald-500/20' : 'bg-rose-500/20'
                      }`}>
                        {mark.mark_type === 'entry' ? (
                          <LogIn className="w-5 h-5 text-emerald-400" />
                        ) : (
                          <LogOut className="w-5 h-5 text-rose-400" />
                        )}
                      </div>
                      <div>
                        <p className="font-medium text-white">
                          {mark.mark_type === 'entry' ? t("geoAttendance.mobile.entry") : t("geoAttendance.mobile.exit")}
                        </p>
                        <p className="text-sm text-slate-400">
                          {mark.location_name}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-mono text-white">{formatTime(mark.timestamp)}</p>
                      <Badge className={getStatusColor(mark.is_within_zone)}>
                        {mark.is_within_zone ? 'OK' : `${Math.round(mark.distance_to_zone)}m`}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* My Locations */}
        {myLocations.length > 0 && (
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center gap-2 text-white">
                <MapPin className="w-5 h-5 text-blue-400" />
                Ubicaciones Autorizadas
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {myLocations.map((loc, idx) => (
                  <div 
                    key={idx} 
                    className="flex items-center justify-between p-3 bg-slate-700/30 rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center">
                        <Building2 className="w-4 h-4 text-blue-400" />
                      </div>
                      <div>
                        <p className="font-medium text-white text-sm">{loc.name}</p>
                        <p className="text-xs text-slate-400">Radio: {loc.radius}m</p>
                      </div>
                    </div>
                    <ChevronRight className="w-5 h-5 text-slate-500" />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
