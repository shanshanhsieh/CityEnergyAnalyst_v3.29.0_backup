import pandas as pd
from geopandas import GeoDataFrame as gdf
import utm
import time
from shapely.geometry import LineString, Point
import random
import networkx as nx
from concept_parameters import *


def calc_substation_location(config, locator):
    #import/ export paths
    input_buildings_shp = locator.get_substation_input_location()
    output_substations_shp = locator.get_substation_output_location()

    poly = gdf.from_file(input_buildings_shp)
    poly = poly.to_crs("+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs")
    lon = poly.geometry[0].centroid.coords.xy[0][0]
    lat = poly.geometry[0].centroid.coords.xy[1][0]

    # get coordinate system and re project to UTM
    utm_data = utm.from_latlon(lat, lon)
    zone = utm_data[2]
    south_or_north = utm_data[3]
    code_projection = "+proj=utm +zone=" + str(zone) + south_or_north + " +ellps=WGS84 +datum=WGS84 +units=m +no_defs"
    poly = poly.to_crs(code_projection)

    # create points
    points = poly.copy()
    points.geometry = poly['geometry'].centroid

    # saving result
    points.to_file(output_substations_shp, driver='ESRI Shapefile')

    return points, poly


def connect_building_to_grid(config, locator):
    #import/ export paths
    input_substations_shp = locator.get_substation_output_location()
    input_streets_shp = locator.get_streets_input_location()

    # Import data
    building_points = gdf.from_file(input_substations_shp)
    lines = gdf.from_file(input_streets_shp)

    # Create DF for points on line
    points_on_line = building_points.copy()
    points_on_line.drop(['floors_bg', 'height_bg', 'floors_ag', 'height_ag', ], axis=1, inplace=True)
    # points_on_line['Node Type'] = None

    for idx, point in points_on_line.iterrows():
        points_on_line.loc[idx, 'Building'] = point['Name']
        # points_on_line.loc[idx, 'Name'] = point['Name'] + ' Coupling Point'

    # Prepare DF for nearest point on line
    building_points['min_dist_to_lines'] = 0
    building_points['nearest_line'] = None

    for idx, point in building_points.iterrows():
        distances = lines.distance(point.geometry)
        nearest_line_idx = distances.idxmin()
        building_points.loc[idx, 'nearest_line'] = nearest_line_idx
        building_points.loc[idx, 'min_dist_to_lines'] = lines.distance(point.geometry).min()

        # find point on nearest line
        project_distances = lines.project(point.geometry)
        project_distance_nearest_line = lines.interpolate(project_distances[nearest_line_idx])
        points_on_line.loc[idx, 'geometry'] = project_distance_nearest_line[nearest_line_idx]

    # Determine Intersections of lines
    for idx, line in lines.iterrows():

        line.geometry = line.geometry.buffer(0.0001)
        line_intersections = lines.intersection(line.geometry)

        for index, intersection in line_intersections.iteritems():
            if intersection.geom_type == 'LineString' and index != idx:
                centroid_buffered = line_intersections[index].centroid.buffer(0.1)  # middle of Linestrings
                if not points_on_line.intersects(centroid_buffered).any():
                    index_points_on_line = points_on_line.shape[0]  # current number of rows in points_on_line
                    points_on_line.loc[index_points_on_line, 'geometry'] = line_intersections[index].centroid
                    points_on_line.loc[index_points_on_line, 'Building'] = None

    # Name Points
    for idx, point in points_on_line.iterrows():
        points_on_line.loc[idx, 'Name'] = 'Node' + str(idx)
        points_on_line.loc[idx, 'Node_int'] = int(idx)

    # Split Linestrings at points_on_line
    tranches_list = []

    for idx, line in lines.iterrows():
        line_buffered = line.copy()
        line_buffered.geometry = line.geometry.buffer(0.0001)
        line_point_intersections = points_on_line.intersection(line_buffered.geometry)
        filtered_points = line_point_intersections[line_point_intersections.is_empty == False]

        start_point = Point(line.values[1].xy[0][0], line.values[1].xy[1][0])

        distance = filtered_points.distance(start_point)
        filtered_points = gdf(data=filtered_points)
        filtered_points['distance'] = distance
        filtered_points.sort_values(by='distance', inplace=True)

        # Create new Lines
        for idx1 in range(0, len(filtered_points)-1):
            start = filtered_points.iloc[idx1][0]
            end = filtered_points.iloc[idx1+1][0]
            newline = LineString([start, end])
            tranches_list.append(newline)

    tranches = gdf(data=tranches_list)
    tranches.columns = ['geometry']
    tranches['Name'] = None
    tranches['Startnode'] = None
    tranches['Endnode'] = None
    tranches['Startnode_int'] = None
    tranches['Endnode_int'] = None
    tranches['Length'] = 0

    for idx, tranch in tranches.iterrows():
        print (idx)
        print (tranch)
        tranches.loc[idx, 'Name'] = 'tranch' + str(idx)
        tranches.loc[idx, 'Length'] = tranch.values[0].length
        print (tranch.values[0].boundary)

        startnode = tranch.values[0].boundary[0]
        endnode = tranch.values[0].boundary[1]

        start_intersection = points_on_line.intersection(startnode.buffer(0.1))
        end_intersection = points_on_line.intersection(endnode.buffer(0.1))
        start_intersection_filtered = start_intersection[start_intersection.is_empty == False]
        end_intersection_filtered = end_intersection[end_intersection.is_empty == False]

        startnode_index = start_intersection_filtered.index.values[0]
        endnode_index = end_intersection_filtered.index.values[0]

        tranches.loc[idx, 'Startnode'] = 'Node' + str(start_intersection_filtered.index.values[0])
        tranches.loc[idx, 'Endnode'] = 'Node' + str(endnode_index)
        tranches.loc[idx, 'Startnode_int'] = int(start_intersection_filtered.index.values[0])
        tranches.loc[idx, 'Endnode_int'] = int(endnode_index)

    # UTM to LAT, LON
    # building_nodes = building_nodes.to_crs("+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs")
    # streets = streets.to_crs("+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs")

    return points_on_line, tranches


def process_network(points_on_line):
    building_path = LOCATOR + SCENARIO + '\\outputs\\data\\demand\\Total_demand.csv'
    building_prop = pd.read_csv(building_path)
    # building_prop = building_prop[['Name', 'GRID0_kW']]
    building_prop.rename(columns={'Name': 'Building'}, inplace=True)

    points_on_line = pd.merge(points_on_line, building_prop, on='Building', how='outer')

    # Declare random plant and  nodes
    points_on_line['Type'] = None
    random.seed(1000)

    for idx, node in points_on_line.iterrows():
            if node['Building'] is not None:
                # if random.random() < 0.08:
                if idx == 0:
                    points_on_line.loc[idx, 'Type'] = 'PLANT'
                else:
                    points_on_line.loc[idx, 'Type'] = 'CONSUMER'

    return points_on_line


def create_length_dict(points_on_line, tranches):
    G_complete = nx.Graph()

    for idx, node in points_on_line.iterrows():
        node_type = node['Type']
        G_complete.add_node(idx, type=node_type)

    for idx, tranch in tranches.iterrows():
        start_node_index = tranch['Startnode'][4::]
        end_node_index = tranch['Endnode'][4::]
        tranch_length = tranch['Length']
        G_complete.add_edge(int(start_node_index), int(end_node_index),
                            weight=tranch_length,
                            gene=idx,
                            startnode=start_node_index,
                            endnode=end_node_index)

    idx_nodes_sub = points_on_line[points_on_line['Type'] == 'PLANT'].index
    idx_nodes_consum = points_on_line[points_on_line['Type'] == 'CONSUMER'].index
    idx_nodes = idx_nodes_sub.append(idx_nodes_consum)

    dict_length = {}
    dict_path = {}
    for idx_node1 in idx_nodes:
        dict_length[idx_node1] = {}
        dict_path[idx_node1] = {}
        for idx_node2 in idx_nodes:
            if idx_node1 == idx_node2:
                dict_length[idx_node1][idx_node2] = 0.0
            else:
                nx.shortest_path(G_complete, 0, 1)
                dict_path[idx_node1][idx_node2] = nx.shortest_path(G_complete,
                                                                   source=idx_node1,
                                                                   target=idx_node2,
                                                                   weight='weight')
                dict_length[idx_node1][idx_node2] = nx.shortest_path_length(G_complete,
                                                                            source=idx_node1,
                                                                            target=idx_node2,
                                                                            weight='weight')
    return dict_length, dict_path


def create_length_complete_dict(points_on_line, tranches):
    G_complete = nx.Graph()

    for idx, node in points_on_line.iterrows():
        node_type = node['Type']
        G_complete.add_node(idx, type=node_type)

    for idx, tranch in tranches.iterrows():
        start_node_index = tranch['Startnode'][4::]
        end_node_index = tranch['Endnode'][4::]
        tranch_length = tranch['Length']
        G_complete.add_edge(int(start_node_index), int(end_node_index),
                            weight=tranch_length,
                            gene=idx,
                            startnode=start_node_index,
                            endnode=end_node_index)

    # idx_nodes_sub = points_on_line[points_on_line['Type'] == 'PLANT'].index
    # idx_nodes_consum = points_on_line[points_on_line['Type'] == 'CONSUMER'].index
    idx_nodes = points_on_line.index

    dict_length = {}
    dict_path = {}
    for idx_node1 in idx_nodes:
        dict_length[idx_node1] = {}
        dict_path[idx_node1] = {}
        for idx_node2 in idx_nodes:
            if idx_node1 == idx_node2:
                dict_length[idx_node1][idx_node2] = 0.0
            else:
                nx.shortest_path(G_complete, 0, 1)
                dict_path[idx_node1][idx_node2] = nx.shortest_path(G_complete,
                                                                   source=idx_node1,
                                                                   target=idx_node2,
                                                                   weight='weight')
                dict_length[idx_node1][idx_node2] = nx.shortest_path_length(G_complete,
                                                                            source=idx_node1,
                                                                            target=idx_node2,
                                                                            weight='weight')
    return dict_length, dict_path


def main():
    calc_substation_location()
    points_on_line, tranches = connect_building_to_grid()
    points_on_line_processed = process_network(points_on_line)
    dict_length, dict_path = create_length_dict(points_on_line_processed, tranches)


if __name__ == '__main__':
    t0 = time.clock()
    main()
    print 'network_optimization_main() succeeded'
    print('total time: ', time.clock() - t0)
