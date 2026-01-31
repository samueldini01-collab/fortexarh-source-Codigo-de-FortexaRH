"""
Fraud Detection Service for Geolocation Attendance
Detección de patrones sospechosos en marcaciones de asistencia
"""
import math
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
from enum import Enum


class AlertLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FraudType(Enum):
    IMPOSSIBLE_SPEED = "impossible_speed"
    DUPLICATE_MARK = "duplicate_mark"
    FREQUENT_OUTSIDE_ZONE = "frequent_outside_zone"
    UNUSUAL_HOURS = "unusual_hours"
    DEVICE_ANOMALY = "device_anomaly"
    GPS_SPOOFING = "gps_spoofing"


# Configuration thresholds
THRESHOLDS = {
    "max_speed_kmh": 150,  # Maximum realistic speed (km/h)
    "duplicate_window_minutes": 5,  # Window to detect duplicate marks
    "outside_zone_threshold": 3,  # Number of outside zone marks to flag
    "unusual_hour_start": 5,  # Before 5am is unusual
    "unusual_hour_end": 23,  # After 11pm is unusual
    "low_accuracy_threshold": 100,  # GPS accuracy > 100m is suspicious
    "min_distance_for_speed_check": 500,  # Minimum distance (m) to check speed
}


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two GPS coordinates in meters"""
    R = 6371000  # Earth's radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c


def calculate_speed_kmh(distance_m: float, time_seconds: float) -> float:
    """Calculate speed in km/h given distance in meters and time in seconds"""
    if time_seconds <= 0:
        return float('inf')
    return (distance_m / 1000) / (time_seconds / 3600)


def detect_impossible_speed(current_mark: Dict, previous_marks: List[Dict]) -> Optional[Dict]:
    """
    Detect if an employee traveled an impossible distance in too short time
    """
    if not previous_marks:
        return None
    
    current_time = datetime.fromisoformat(current_mark["timestamp"].replace("Z", "+00:00"))
    current_lat = current_mark["latitude"]
    current_lon = current_mark["longitude"]
    
    for prev_mark in previous_marks:
        prev_time = datetime.fromisoformat(prev_mark["timestamp"].replace("Z", "+00:00"))
        time_diff = (current_time - prev_time).total_seconds()
        
        # Only check marks within last 2 hours
        if time_diff > 7200 or time_diff < 60:
            continue
        
        prev_lat = prev_mark["latitude"]
        prev_lon = prev_mark["longitude"]
        
        distance = haversine_distance(current_lat, current_lon, prev_lat, prev_lon)
        
        # Only check if distance is significant
        if distance < THRESHOLDS["min_distance_for_speed_check"]:
            continue
        
        speed = calculate_speed_kmh(distance, time_diff)
        
        if speed > THRESHOLDS["max_speed_kmh"]:
            return {
                "type": FraudType.IMPOSSIBLE_SPEED.value,
                "level": AlertLevel.CRITICAL.value if speed > 300 else AlertLevel.HIGH.value,
                "details": {
                    "calculated_speed_kmh": round(speed, 2),
                    "max_allowed_kmh": THRESHOLDS["max_speed_kmh"],
                    "distance_km": round(distance / 1000, 2),
                    "time_minutes": round(time_diff / 60, 2),
                    "previous_location": {
                        "lat": prev_lat,
                        "lon": prev_lon,
                        "name": prev_mark.get("location_name", "Desconocido"),
                        "time": prev_mark["timestamp"]
                    },
                    "current_location": {
                        "lat": current_lat,
                        "lon": current_lon,
                        "name": current_mark.get("location_name", "Desconocido"),
                        "time": current_mark["timestamp"]
                    }
                },
                "message": f"Velocidad imposible detectada: {round(speed, 1)} km/h ({round(distance/1000, 1)}km en {round(time_diff/60, 1)} min)"
            }
    
    return None


def detect_duplicate_mark(current_mark: Dict, recent_marks: List[Dict]) -> Optional[Dict]:
    """
    Detect duplicate marks within a short time window
    """
    if not recent_marks:
        return None
    
    current_time = datetime.fromisoformat(current_mark["timestamp"].replace("Z", "+00:00"))
    window = timedelta(minutes=THRESHOLDS["duplicate_window_minutes"])
    
    for mark in recent_marks:
        if mark.get("mark_id") == current_mark.get("mark_id"):
            continue
            
        mark_time = datetime.fromisoformat(mark["timestamp"].replace("Z", "+00:00"))
        
        if abs(current_time - mark_time) < window:
            if mark["mark_type"] == current_mark["mark_type"]:
                return {
                    "type": FraudType.DUPLICATE_MARK.value,
                    "level": AlertLevel.MEDIUM.value,
                    "details": {
                        "time_diff_seconds": abs((current_time - mark_time).total_seconds()),
                        "previous_mark_id": mark.get("mark_id"),
                        "mark_type": current_mark["mark_type"]
                    },
                    "message": f"Marcación duplicada detectada en menos de {THRESHOLDS['duplicate_window_minutes']} minutos"
                }
    
    return None


def detect_unusual_hours(current_mark: Dict) -> Optional[Dict]:
    """
    Detect marks at unusual hours
    """
    timestamp = datetime.fromisoformat(current_mark["timestamp"].replace("Z", "+00:00"))
    hour = timestamp.hour
    
    if hour < THRESHOLDS["unusual_hour_start"] or hour >= THRESHOLDS["unusual_hour_end"]:
        return {
            "type": FraudType.UNUSUAL_HOURS.value,
            "level": AlertLevel.LOW.value,
            "details": {
                "hour": hour,
                "expected_range": f"{THRESHOLDS['unusual_hour_start']}:00 - {THRESHOLDS['unusual_hour_end']}:00"
            },
            "message": f"Marcación en horario inusual: {hour}:00 hrs"
        }
    
    return None


def detect_gps_spoofing(current_mark: Dict) -> Optional[Dict]:
    """
    Detect potential GPS spoofing based on accuracy and other indicators
    """
    accuracy = current_mark.get("accuracy", 0)
    
    # Very low accuracy might indicate GPS issues or spoofing
    if accuracy > THRESHOLDS["low_accuracy_threshold"]:
        return {
            "type": FraudType.GPS_SPOOFING.value,
            "level": AlertLevel.MEDIUM.value,
            "details": {
                "reported_accuracy": accuracy,
                "threshold": THRESHOLDS["low_accuracy_threshold"]
            },
            "message": f"Precisión GPS baja detectada: {accuracy}m (umbral: {THRESHOLDS['low_accuracy_threshold']}m)"
        }
    
    # Check for suspiciously perfect coordinates (might indicate fake GPS apps)
    lat = current_mark.get("latitude", 0)
    lon = current_mark.get("longitude", 0)
    
    # Perfect round numbers are suspicious
    if lat == round(lat, 2) and lon == round(lon, 2) and accuracy < 5:
        return {
            "type": FraudType.GPS_SPOOFING.value,
            "level": AlertLevel.MEDIUM.value,
            "details": {
                "latitude": lat,
                "longitude": lon,
                "accuracy": accuracy
            },
            "message": "Coordenadas sospechosamente exactas con alta precisión reportada"
        }
    
    return None


def analyze_outside_zone_pattern(employee_marks: List[Dict], days: int = 7) -> Optional[Dict]:
    """
    Analyze if an employee frequently marks outside authorized zones
    """
    if not employee_marks:
        return None
    
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    recent_marks = []
    
    for mark in employee_marks:
        mark_time = datetime.fromisoformat(mark["timestamp"].replace("Z", "+00:00"))
        if mark_time > cutoff:
            recent_marks.append(mark)
    
    if len(recent_marks) < 3:
        return None
    
    outside_count = sum(1 for m in recent_marks if not m.get("is_within_zone", True))
    
    if outside_count >= THRESHOLDS["outside_zone_threshold"]:
        percentage = (outside_count / len(recent_marks)) * 100
        return {
            "type": FraudType.FREQUENT_OUTSIDE_ZONE.value,
            "level": AlertLevel.HIGH.value if percentage > 50 else AlertLevel.MEDIUM.value,
            "details": {
                "outside_zone_count": outside_count,
                "total_marks": len(recent_marks),
                "percentage": round(percentage, 1),
                "period_days": days
            },
            "message": f"Patrón de marcaciones fuera de zona: {outside_count}/{len(recent_marks)} ({round(percentage, 1)}%) en {days} días"
        }
    
    return None


def run_fraud_detection(current_mark: Dict, previous_marks: List[Dict], employee_history: List[Dict] = None) -> List[Dict]:
    """
    Run all fraud detection checks on a mark
    Returns list of detected fraud alerts
    """
    alerts = []
    
    # Check for impossible speed
    speed_alert = detect_impossible_speed(current_mark, previous_marks)
    if speed_alert:
        alerts.append(speed_alert)
    
    # Check for duplicate marks
    duplicate_alert = detect_duplicate_mark(current_mark, previous_marks)
    if duplicate_alert:
        alerts.append(duplicate_alert)
    
    # Check for unusual hours
    hours_alert = detect_unusual_hours(current_mark)
    if hours_alert:
        alerts.append(hours_alert)
    
    # Check for GPS spoofing
    gps_alert = detect_gps_spoofing(current_mark)
    if gps_alert:
        alerts.append(gps_alert)
    
    # Check outside zone if mark is outside
    if not current_mark.get("is_within_zone", True):
        alerts.append({
            "type": "outside_zone",
            "level": AlertLevel.LOW.value,
            "details": {
                "distance_to_zone": current_mark.get("distance_to_zone", 0),
                "location_name": current_mark.get("location_name", "Fuera de zona")
            },
            "message": f"Marcación fuera de zona autorizada ({round(current_mark.get('distance_to_zone', 0), 0)}m de distancia)"
        })
    
    # Check pattern if history provided
    if employee_history:
        pattern_alert = analyze_outside_zone_pattern(employee_history)
        if pattern_alert:
            alerts.append(pattern_alert)
    
    return alerts


def get_alert_priority_score(alert: Dict) -> int:
    """Get numeric priority score for sorting alerts"""
    level_scores = {
        AlertLevel.CRITICAL.value: 100,
        AlertLevel.HIGH.value: 75,
        AlertLevel.MEDIUM.value: 50,
        AlertLevel.LOW.value: 25
    }
    return level_scores.get(alert.get("level", "low"), 0)


def summarize_alerts(alerts: List[Dict]) -> Dict:
    """Create a summary of alerts by level and type"""
    summary = {
        "total": len(alerts),
        "by_level": {
            AlertLevel.CRITICAL.value: 0,
            AlertLevel.HIGH.value: 0,
            AlertLevel.MEDIUM.value: 0,
            AlertLevel.LOW.value: 0
        },
        "by_type": {},
        "highest_level": AlertLevel.LOW.value
    }
    
    for alert in alerts:
        level = alert.get("level", AlertLevel.LOW.value)
        alert_type = alert.get("type", "unknown")
        
        summary["by_level"][level] = summary["by_level"].get(level, 0) + 1
        summary["by_type"][alert_type] = summary["by_type"].get(alert_type, 0) + 1
    
    # Determine highest level
    for level in [AlertLevel.CRITICAL.value, AlertLevel.HIGH.value, AlertLevel.MEDIUM.value, AlertLevel.LOW.value]:
        if summary["by_level"].get(level, 0) > 0:
            summary["highest_level"] = level
            break
    
    return summary
