import os
import pyproj
import geopandas as gpd
from shapely.geometry import Point

class Node():
    def __init__(self,x,y):
        self.x=x
        self.y=y

# compute x,y coordenates
def generate_random_location(district,random_numpy):
    x,y = __generate_random_location_within_ROI(1,district,random_numpy)
    #print("localization:",x[0],y[0])
    return x[0],y[0]

def get_district(file,district):
    # districts = gpd.read_file(file)
    # df = districts[districts["BARRI"]=='71']#districts[districts["NOM"] == district]  # .plot(figsize=(10,6))
    # df.to_file('district.geojson', driver='GeoJSON')
    df = gpd.read_file("inputs" + os.sep + "map_bcn.json")
    return df[df['NOM'] == district]

def __tranform_coordinates(x,y):
    # Define the source CRS (EPSG:25831)
    source_crs = pyproj.CRS.from_epsg(25831)

    # Define the target CRS (EPSG:4326 for WGS 84, which is commonly used for lat/lon)
    target_crs = pyproj.CRS.from_epsg(4326)

    # Create a transformer to convert coordinates
    transformer = pyproj.Transformer.from_crs(source_crs, target_crs, always_xy=True)

    # Perform the conversion
    lon, lat = transformer.transform(x,y)
    return lon, lat

def __generate_random_location_within_ROI(num_pt, district,random_numpy):
    """
    Generate num_pt random location coordinates .
    :param num_pt INT number of random location coordinates
    :param polygon geopandas.geoseries.GeoSeries the polygon of the region
    :return x, y lists of location coordinates, longetude and latitude
    """
    # define boundaries
    bounds_all = district.bounds
    minx = min(bounds_all.minx)
    maxx = max(bounds_all.maxx)
    miny = min(bounds_all.miny)
    maxy = max(bounds_all.maxy)

    i,x,y = 0, [],[]

    while i < num_pt:
    # generate random location coordinates
        try:
            x_t = random_numpy.uniform(minx, maxx)
            y_t = random_numpy.uniform(miny, maxy)

            # further check whether it is in the city area
            for p in district['geometry']:
                if Point(x_t, y_t).within(p):
                    lon,lat = __tranform_coordinates(x_t,y_t)
                    x.append(lon)
                    y.append(lat)
                    i = i + 1
        except:
            print(minx, maxx, miny, maxy)

    return x, y


# def get_route(self, pickup_lat, pickup_lon, dropoff_lat, dropoff_lon):
#     loc = "{},{};{},{}".format(pickup_lon, pickup_lat, dropoff_lon, dropoff_lat)
#     url = "http://router.project-osrm.org/route/v1/driving/"
#     r = requests.get(url + loc)
#     if r.status_code != 200:
#         return {}
#
#     res = r.json()
#     routes = polyline.decode(res['routes'][0]['geometry'])
#     start_point = [res['waypoints'][0]['location'][1], res['waypoints'][0]['location'][0]]
#     end_point = [res['waypoints'][1]['location'][1], res['waypoints'][1]['location'][0]]
#     distance = res['routes'][0]['distance']
#
#     out = {'route': routes,
#            'start_point': start_point,
#            'end_point': end_point,
#            'distance': distance
#            }
#
#     return out
#
#
# def get_map(self, routes):
#     m = folium.Map(location=[(routes[0][0]['start_point'][0] + routes[0][0]['end_point'][0]) / 2,
#                              (routes[0][0]['start_point'][1] + routes[0][0]['end_point'][1]) / 2],
#                    zoom_start=8)
#
#     # https: // matplotlib.org / 3.1.0 / gallery / color / named_colors.html
#     colors = list(mcolors.CSS4_COLORS)
#
#     for route in routes:
#
#         color = colors[random.randint(0, len(colors) - 1)]
#         for leg in route:
#             folium.PolyLine(
#                 leg['route'],
#                 weight=8,
#                 color=color,
#                 opacity=0.6
#             ).add_to(m)
#
#             folium.Marker(
#                 location=leg['start_point'],
#                 icon=folium.Icon(icon='play', color='green')
#             ).add_to(m)
#
#             folium.Marker(
#                 location=leg['end_point'],
#                 icon=folium.Icon(icon='stop', color='red')
#             ).add_to(m)
#
#     return m
#
#
# def createHTMLRoutes(self, path, name, list_routes=[]):
#     routes_geo = []
#     for aRoute in self.routes:
#         route = []
#         for edge in aRoute.edges:
#             leg_geo = self.get_route(edge.origin.x, edge.origin.y, edge.end.x, edge.end.y)
#             route.append(leg_geo)
#
#         routes_geo.append(route)
#
#     m = self.get_map(routes_geo)
#     m.save(path + os.sep + name + '_routes.html')