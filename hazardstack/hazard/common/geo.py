"""Geospatial utilities using H3 hexagonal grid."""

import h3
import numpy as np
from typing import List, Tuple, Set, Optional
from shapely.geometry import Polygon, Point, box
import geopandas as gpd
from pyproj import Transformer


class H3Grid:
    """H3 hexagonal grid for India."""

    def __init__(self, resolution: int = 4, bounds: Optional[dict] = None):
        """
        Initialize H3 grid.

        Args:
            resolution: H3 resolution (0-15). 4 = ~5-10 km, 5 = ~2-3 km
            bounds: Dict with lat_min, lat_max, lon_min, lon_max
        """
        self.resolution = resolution

        # Default to India bounds
        if bounds is None:
            bounds = {
                "lat_min": 6.5,
                "lat_max": 35.5,
                "lon_min": 68.0,
                "lon_max": 97.5,
            }
        self.bounds = bounds

        # Generate cells covering India
        self.cells = self._generate_cells()
        self.cell_to_latlon = {cell: h3.h3_to_geo(cell) for cell in self.cells}

    def _generate_cells(self) -> Set[str]:
        """Generate H3 cells covering the bounding box."""
        cells = set()

        # Create a bounding polygon
        bounds = self.bounds
        bbox = box(
            bounds["lon_min"],
            bounds["lat_min"],
            bounds["lon_max"],
            bounds["lat_max"],
        )

        # Sample points in the bounding box and get their H3 cells
        lats = np.linspace(bounds["lat_min"], bounds["lat_max"], 100)
        lons = np.linspace(bounds["lon_min"], bounds["lon_max"], 100)

        for lat in lats:
            for lon in lons:
                cell = h3.geo_to_h3(lat, lon, self.resolution)
                cells.add(cell)

        return cells

    def load_from_geojson(self, geojson_path: str) -> Set[str]:
        """
        Load cells that intersect with a GeoJSON polygon (e.g., India boundary).

        Args:
            geojson_path: Path to GeoJSON file

        Returns:
            Set of H3 cell IDs
        """
        gdf = gpd.read_file(geojson_path)
        cells = set()

        for geom in gdf.geometry:
            # Get cells at boundary and fill
            if geom.geom_type == "Polygon":
                cells.update(self._polyfill_polygon(geom))
            elif geom.geom_type == "MultiPolygon":
                for poly in geom.geoms:
                    cells.update(self._polyfill_polygon(poly))

        self.cells = cells
        self.cell_to_latlon = {cell: h3.h3_to_geo(cell) for cell in cells}
        return cells

    def _polyfill_polygon(self, polygon: Polygon) -> Set[str]:
        """Fill a polygon with H3 cells using h3-py polyfill."""
        # Convert shapely polygon to GeoJSON-like structure
        coords = list(polygon.exterior.coords)
        geojson_coords = [(lon, lat) for lat, lon in coords]

        # h3.polyfill requires GeoJSON format
        geojson = {"type": "Polygon", "coordinates": [geojson_coords]}

        try:
            cells = h3.polyfill_geojson(geojson, self.resolution)
        except:
            # Fallback: sample points in polygon
            cells = set()
            minx, miny, maxx, maxy = polygon.bounds
            lats = np.linspace(miny, maxy, 50)
            lons = np.linspace(minx, maxx, 50)
            for lat in lats:
                for lon in lons:
                    if polygon.contains(Point(lon, lat)):
                        cells.add(h3.geo_to_h3(lat, lon, self.resolution))

        return cells

    def get_neighbors(self, cell: str, k: int = 1) -> List[str]:
        """
        Get k-ring neighbors of a cell.

        Args:
            cell: H3 cell ID
            k: Ring distance (1 = immediate neighbors)

        Returns:
            List of neighbor cell IDs
        """
        return list(h3.k_ring(cell, k))

    def get_distance_km(self, cell1: str, cell2: str) -> float:
        """
        Get great-circle distance between two cells in km.

        Args:
            cell1: First H3 cell ID
            cell2: Second H3 cell ID

        Returns:
            Distance in kilometers
        """
        lat1, lon1 = h3.h3_to_geo(cell1)
        lat2, lon2 = h3.h3_to_geo(cell2)
        return self._haversine(lat1, lon1, lat2, lon2)

    def cells_within_radius(self, lat: float, lon: float, radius_km: float) -> List[str]:
        """
        Get all cells within a radius of a point.

        Args:
            lat: Latitude
            lon: Longitude
            radius_km: Radius in kilometers

        Returns:
            List of H3 cell IDs
        """
        center_cell = h3.geo_to_h3(lat, lon, self.resolution)

        # Estimate k-ring size needed
        # Average H3 edge length at resolution 4 is ~5.16 km
        edge_length_km = h3.edge_length(self.resolution, unit="km")
        k = int(np.ceil(radius_km / edge_length_km)) + 1

        candidates = h3.k_ring(center_cell, k)

        # Filter by actual distance
        result = []
        for cell in candidates:
            cell_lat, cell_lon = h3.h3_to_geo(cell)
            if self._haversine(lat, lon, cell_lat, cell_lon) <= radius_km:
                result.append(cell)

        return result

    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate Haversine distance in km."""
        R = 6371.0  # Earth radius in km

        lat1_rad = np.radians(lat1)
        lat2_rad = np.radians(lat2)
        delta_lat = np.radians(lat2 - lat1)
        delta_lon = np.radians(lon2 - lon1)

        a = (
            np.sin(delta_lat / 2) ** 2
            + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(delta_lon / 2) ** 2
        )
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

        return R * c

    def get_cell_area_km2(self, cell: str) -> float:
        """Get area of a cell in km^2."""
        return h3.cell_area(cell, unit="km^2")

    def to_geopandas(self) -> gpd.GeoDataFrame:
        """Convert grid to GeoDataFrame for visualization."""
        geometries = []
        h3_ids = []

        for cell in self.cells:
            boundary = h3.h3_to_geo_boundary(cell, geo_json=True)
            # Convert from (lon, lat) to (lat, lon) for Shapely
            coords = [(lon, lat) for lat, lon in boundary]
            poly = Polygon(coords)
            geometries.append(poly)
            h3_ids.append(cell)

        gdf = gpd.GeoDataFrame({"h3_id": h3_ids, "geometry": geometries}, crs="EPSG:4326")
        return gdf


class BasinGraph:
    """River basin topology as a directed graph."""

    def __init__(self):
        """Initialize empty basin graph."""
        self.basins = {}  # basin_id -> BasinInfo
        self.adjacency = {}  # basin_id -> [downstream_basin_ids]
        self.reverse_adjacency = {}  # basin_id -> [upstream_basin_ids]

    def add_basin(
        self,
        basin_id: str,
        name: str,
        area_km2: float,
        mean_elevation_m: float,
        danger_threshold_m3s: Optional[float] = None,
    ):
        """Add a basin to the graph."""
        self.basins[basin_id] = {
            "basin_id": basin_id,
            "name": name,
            "area_km2": area_km2,
            "mean_elevation_m": mean_elevation_m,
            "danger_threshold_m3s": danger_threshold_m3s,
            "upstream_basins": [],
        }
        self.adjacency[basin_id] = []
        self.reverse_adjacency[basin_id] = []

    def add_flow(self, upstream_id: str, downstream_id: str):
        """Add a flow connection from upstream to downstream basin."""
        if upstream_id not in self.basins or downstream_id not in self.basins:
            raise ValueError("Both basins must be added before connecting them")

        self.adjacency[upstream_id].append(downstream_id)
        self.reverse_adjacency[downstream_id].append(upstream_id)
        self.basins[downstream_id]["upstream_basins"].append(upstream_id)

    def get_upstream_basins(self, basin_id: str, recursive: bool = True) -> List[str]:
        """
        Get all upstream basins.

        Args:
            basin_id: Basin ID
            recursive: If True, get all upstream basins recursively

        Returns:
            List of upstream basin IDs
        """
        if not recursive:
            return self.reverse_adjacency.get(basin_id, [])

        # BFS to find all upstream
        visited = set()
        queue = [basin_id]

        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)

            upstream = self.reverse_adjacency.get(current, [])
            queue.extend(upstream)

        visited.discard(basin_id)  # Remove self
        return list(visited)

    def get_downstream_basins(self, basin_id: str, recursive: bool = True) -> List[str]:
        """Get all downstream basins."""
        if not recursive:
            return self.adjacency.get(basin_id, [])

        # BFS to find all downstream
        visited = set()
        queue = [basin_id]

        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)

            downstream = self.adjacency.get(current, [])
            queue.extend(downstream)

        visited.discard(basin_id)
        return list(visited)

    def topological_sort(self) -> List[str]:
        """
        Return basins in topological order (upstream to downstream).

        Returns:
            List of basin IDs in topological order
        """
        in_degree = {basin_id: 0 for basin_id in self.basins}

        for basin_id in self.basins:
            for downstream_id in self.adjacency[basin_id]:
                in_degree[downstream_id] += 1

        # Start with basins that have no upstream (in_degree = 0)
        queue = [basin_id for basin_id, deg in in_degree.items() if deg == 0]
        result = []

        while queue:
            current = queue.pop(0)
            result.append(current)

            for downstream_id in self.adjacency[current]:
                in_degree[downstream_id] -= 1
                if in_degree[downstream_id] == 0:
                    queue.append(downstream_id)

        if len(result) != len(self.basins):
            raise ValueError("Graph has a cycle!")

        return result
