import { useEffect, useRef } from "react";
import { MapContainer, TileLayer, Circle, Marker, Popup, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { Badge } from "@/components/ui/badge";
import { Clock, MapPin, User, AlertTriangle, CheckCircle } from "lucide-react";

// Fix for default marker icons in React-Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png",
  iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
});

// Custom icons for different states
const createCustomIcon = (color) => {
  return L.divIcon({
    className: "custom-marker",
    html: `
      <div style="
        background-color: ${color};
        width: 32px;
        height: 32px;
        border-radius: 50% 50% 50% 0;
        transform: rotate(-45deg);
        border: 3px solid white;
        box-shadow: 0 2px 5px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        justify-content: center;
      ">
        <div style="
          transform: rotate(45deg);
          color: white;
          font-size: 14px;
          font-weight: bold;
        ">👤</div>
      </div>
    `,
    iconSize: [32, 32],
    iconAnchor: [16, 32],
    popupAnchor: [0, -32],
  });
};

const greenIcon = createCustomIcon("#10b981");
const yellowIcon = createCustomIcon("#f59e0b");
const redIcon = createCustomIcon("#ef4444");
const blueIcon = createCustomIcon("#3b82f6");

// Component to fit bounds
function FitBounds({ locations, employees }) {
  const map = useMap();
  
  useEffect(() => {
    const allPoints = [
      ...locations.map(loc => [loc.latitude, loc.longitude]),
      ...employees.map(emp => [emp.latitude, emp.longitude])
    ];
    
    if (allPoints.length > 0) {
      const bounds = L.latLngBounds(allPoints);
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 15 });
    }
  }, [locations, employees, map]);
  
  return null;
}

// Main GeoMap component
export default function GeoMap({ 
  locations = [], 
  employees = [], 
  onEmployeeClick,
  onLocationClick,
  selectedLocation = null,
  height = "500px",
  showLegend = true
}) {
  // Default center (Santo Domingo, Dominican Republic)
  const defaultCenter = [18.4861, -69.9312];
  const defaultZoom = 13;
  
  // Get center based on locations or use default
  const getCenter = () => {
    if (locations.length > 0) {
      const avgLat = locations.reduce((sum, loc) => sum + loc.latitude, 0) / locations.length;
      const avgLng = locations.reduce((sum, loc) => sum + loc.longitude, 0) / locations.length;
      return [avgLat, avgLng];
    }
    return defaultCenter;
  };

  // Get icon based on employee status
  const getEmployeeIcon = (employee) => {
    if (employee.status === "rejected") return redIcon;
    if (!employee.is_within_zone) return yellowIcon;
    return greenIcon;
  };

  // Get circle color for geofence
  const getGeofenceColor = (location) => {
    if (selectedLocation && selectedLocation.location_id === location.location_id) {
      return "#3b82f6"; // Blue for selected
    }
    return location.is_active ? "#10b981" : "#9ca3af"; // Green for active, gray for inactive
  };

  // Format time
  const formatTime = (timestamp) => {
    if (!timestamp) return "";
    return new Date(timestamp).toLocaleTimeString("es-DO", { hour: "2-digit", minute: "2-digit" });
  };

  return (
    <div className="relative" style={{ height }}>
      <MapContainer
        center={getCenter()}
        zoom={defaultZoom}
        style={{ height: "100%", width: "100%", borderRadius: "0.5rem" }}
        className="z-0"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        {/* Fit bounds to show all markers */}
        {(locations.length > 0 || employees.length > 0) && (
          <FitBounds locations={locations} employees={employees} />
        )}
        
        {/* Geofence circles */}
        {locations.map((location) => (
          <Circle
            key={location.location_id}
            center={[location.latitude, location.longitude]}
            radius={location.radius}
            pathOptions={{
              color: getGeofenceColor(location),
              fillColor: getGeofenceColor(location),
              fillOpacity: 0.2,
              weight: 2,
            }}
            eventHandlers={{
              click: () => onLocationClick && onLocationClick(location),
            }}
          >
            <Popup>
              <div className="min-w-[200px]">
                <div className="flex items-center gap-2 mb-2">
                  <MapPin className="w-4 h-4 text-blue-600" />
                  <span className="font-semibold">{location.name}</span>
                </div>
                <p className="text-sm text-gray-600 mb-1">{location.address}</p>
                <div className="flex items-center gap-2 text-xs text-gray-500">
                  <span>Radio: {location.radius}m</span>
                  <span>•</span>
                  <span>{location.employee_count || 0} empleados</span>
                </div>
                {location.is_active ? (
                  <Badge className="mt-2 bg-green-100 text-green-700">Activa</Badge>
                ) : (
                  <Badge className="mt-2 bg-gray-100 text-gray-700">Inactiva</Badge>
                )}
              </div>
            </Popup>
          </Circle>
        ))}
        
        {/* Location center markers */}
        {locations.map((location) => (
          <Marker
            key={`center-${location.location_id}`}
            position={[location.latitude, location.longitude]}
            icon={blueIcon}
          >
            <Popup>
              <div className="font-semibold">{location.name}</div>
              <div className="text-sm text-gray-500">{location.address}</div>
            </Popup>
          </Marker>
        ))}
        
        {/* Employee markers */}
        {employees.map((employee, idx) => (
          <Marker
            key={employee.mark_id || idx}
            position={[employee.latitude, employee.longitude]}
            icon={getEmployeeIcon(employee)}
            eventHandlers={{
              click: () => onEmployeeClick && onEmployeeClick(employee),
            }}
          >
            <Popup>
              <div className="min-w-[220px]">
                <div className="flex items-center gap-2 mb-2">
                  <User className="w-4 h-4 text-slate-600" />
                  <span className="font-semibold">{employee.employee_name}</span>
                </div>
                
                <div className="space-y-1 text-sm">
                  <div className="flex items-center gap-2">
                    <Clock className="w-3 h-3 text-gray-400" />
                    <span>
                      {employee.mark_type === "entry" ? "Entrada" : "Salida"}: {formatTime(employee.timestamp)}
                    </span>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <MapPin className="w-3 h-3 text-gray-400" />
                    <span>{employee.location_name}</span>
                  </div>
                  
                  {!employee.is_within_zone && (
                    <div className="flex items-center gap-2 text-amber-600">
                      <AlertTriangle className="w-3 h-3" />
                      <span>{Math.round(employee.distance_to_zone)}m fuera de zona</span>
                    </div>
                  )}
                </div>
                
                <div className="mt-2">
                  {employee.is_within_zone ? (
                    <Badge className="bg-green-100 text-green-700">
                      <CheckCircle className="w-3 h-3 mr-1" />
                      Dentro de zona
                    </Badge>
                  ) : employee.status === "pending_review" ? (
                    <Badge className="bg-amber-100 text-amber-700">
                      <AlertTriangle className="w-3 h-3 mr-1" />
                      Pendiente revisión
                    </Badge>
                  ) : employee.status === "rejected" ? (
                    <Badge className="bg-red-100 text-red-700">Rechazada</Badge>
                  ) : (
                    <Badge className="bg-green-100 text-green-700">Aprobada</Badge>
                  )}
                </div>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
      
      {/* Legend */}
      {showLegend && (
        <div className="absolute bottom-4 left-4 bg-white dark:bg-slate-800 rounded-lg shadow-lg p-3 z-[1000]">
          <div className="text-xs font-semibold mb-2 text-slate-700 dark:text-slate-300">Leyenda</div>
          <div className="space-y-1.5 text-xs">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-emerald-500"></div>
              <span className="text-slate-600 dark:text-slate-400">Dentro de zona</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-amber-500"></div>
              <span className="text-slate-600 dark:text-slate-400">Fuera de zona</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500"></div>
              <span className="text-slate-600 dark:text-slate-400">Rechazada</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-blue-500"></div>
              <span className="text-slate-600 dark:text-slate-400">Ubicación</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full border-2 border-emerald-500 bg-emerald-500/20"></div>
              <span className="text-slate-600 dark:text-slate-400">Geofence</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
