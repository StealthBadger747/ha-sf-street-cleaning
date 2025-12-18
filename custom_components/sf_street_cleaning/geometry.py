import math

def distance_point_to_segment_meters(px, py, x1, y1, x2, y2):
    """
    Calculates the perpendicular distance from point (px, py) to the line segment (x1, y1)-(x2, y2)
    in meters. Inputs are in degrees (lat/lon).
    px, py: point lon, lat
    x1, y1: segment start lon, lat
    x2, y2: segment end lon, lat
    """
    # 1 degree lat ~ 111,139 meters
    # 1 degree lon ~ 111,139 * cos(lat) meters
    METERS_PER_DEG_LAT = 111139.0
    # Use average latitude of the segment for longitude conversion
    avg_lat_rad = math.radians((y1 + y2) / 2.0)
    meters_per_deg_lon = 111139.0 * math.cos(avg_lat_rad)

    # Convert everything to meters relative to the point (px, py)
    # Let P be (0, 0)
    X1 = (x1 - px) * meters_per_deg_lon
    Y1 = (y1 - py) * METERS_PER_DEG_LAT
    X2 = (x2 - px) * meters_per_deg_lon
    Y2 = (y2 - py) * METERS_PER_DEG_LAT

    # Vector V = P2 - P1 = (X2 - X1, Y2 - Y1)
    dx = X2 - X1
    dy = Y2 - Y1

    if dx == 0 and dy == 0:
        return math.sqrt(X1*X1 + Y1*Y1)

    # Project point P(0,0) onto line passing through P1, P2
    # The parameter t for the projection point on the infinite line
    # P(t) = P1 + t * V
    # Vector P1 = (X1, Y1)
    # We want (P - P(t)) dot V = 0
    # (-P1 - tV) dot V = 0
    # - (P1 dot V) / (V dot V) = t
    t = - (X1 * dx + Y1 * dy) / (dx * dx + dy * dy)

    # Clamp t to segment [0, 1]
    t = max(0, min(1, t))

    # Closest point on segment
    closest_x = X1 + t * dx
    closest_y = Y1 + t * dy

    # Distance
    dist = math.sqrt(closest_x*closest_x + closest_y*closest_y)
    return dist

def get_bearing(lat1, lon1, lat2, lon2):
    """
    Calculates the bearing from point 1 to point 2 in degrees (0-360).
    """
    y = math.sin(math.radians(lon2 - lon1)) * math.cos(math.radians(lat2))
    x = math.cos(math.radians(lat1)) * math.sin(math.radians(lat2)) - \
        math.sin(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.cos(math.radians(lon2 - lon1))
    bearing = math.degrees(math.atan2(y, x))
    return (bearing + 360) % 360

def find_cleaning_data(geojson, lat, lon, rotation):
    """
    Finds the closest street segment and determines the side.
    Returns a dictionary with street info or None.
    """
    if not geojson or 'features' not in geojson:
        return None

    closest_feature = None
    min_dist = float("inf")
    closest_segment_bearing = 0
    
    # Iterate through features
    for feature in geojson['features']:
        geometry = feature.get('geometry')
        if not geometry or geometry['type'] != 'LineString':
            continue

        coords = geometry['coordinates']
        # Iterate segments
        for i in range(len(coords) - 1):
            p1 = coords[i]   # [lon, lat]
            p2 = coords[i+1] # [lon, lat]
            
            # Distance logic
            dist = distance_point_to_segment_meters(lon, lat, p1[0], p1[1], p2[0], p2[1])
            
            if dist < min_dist:
                min_dist = dist
                closest_feature = feature
                # Calculate bearing of the street segment
                closest_segment_bearing = get_bearing(p1[1], p1[0], p2[1], p2[0])

    if not closest_feature:
        return None

    props = closest_feature['properties']
    street_name = props.get('streetname', props.get('Corridor', props.get('StreetIdentifier', 'Unknown')))
    
    # Side detection logic
    side = "Unknown"
    is_median = False
    
    # 1. Median Check (very close to center)
    if min_dist < 6.0: 
         if "Median" in props.get("Sides", {}):
             is_median = True
             side = "Median"
    
    detected_side_key = None
    
    if is_median:
         detected_side_key = "Median"
    else:
        # 2. Heading-based Side Logic
        # Normalize bearing to 0-360
        street_bearing = closest_segment_bearing
        
        # Determine strict cardinal side of the street relative to the line
        # Logic adapted from 'main.py'
        
        # Determine if street is roughly North-South or East-West
        # N-S: Bearings 315-45 OR 135-225
        is_ns_street = (315 <= street_bearing or street_bearing < 45) or (135 <= street_bearing < 225)
        
        if is_ns_street:
             # North-South Street
             # 0=North, 90=East, 180=South, 270=West
             if rotation < 90 or rotation > 270: # Heading North-ish
                 detected_side_key = "East"      # Right side of N-bound traffic is East
             elif 90 < rotation < 270:           # Heading South-ish
                 detected_side_key = "West"      # Right side of S-bound traffic is West
        else:
            # East-West Street
            if rotation < 180: # Heading North/East (0-180) -> mostly East-ish for E-W street
                 detected_side_key = "South" # Right side of E-bound traffic is South
            else:
                 detected_side_key = "North" # Right side of W-bound traffic is North

    # Fallback/Validation
    cleaning_info = None
    available_sides = list(props.get('Sides', {}).keys())
    
    if detected_side_key and detected_side_key in props.get('Sides', {}):
        cleaning_info = props['Sides'][detected_side_key]
        side = detected_side_key
    elif len(available_sides) > 0:
        # Default to first available if detection fails
        side = f"{available_sides[0]} (Defaulted)"
        cleaning_info = props['Sides'][available_sides[0]]

    return {
        "street": street_name,
        "nextCleaning": cleaning_info,
        "parkedOnSide": side,
        "distance": min_dist,
        "median": is_median
    }
