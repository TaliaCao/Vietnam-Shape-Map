import geopandas as gpd
import pandas as pd
from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import unary_union
from pykml.factory import KML_ElementMaker as KML
from lxml import etree
import uuid

# Define the mapping table
mapping_table = {
    'An Giang': ['An Giang', 'Kien Giang'],
    'Bắc Ninh': ['Bắc Ninh', 'Bắc Giang'],
    'Cà Mau': ['Bạc Liêu', 'Cà Mau'],
    'TP Cần Thơ': ['Cần Thơn', 'Sóc Trăng', 'Hậu Giang'],
    'Cao Bằng': ['Cao Bằng'],
    'TP Đà Nẵng': ['Quảng Nam', 'Đà Nẵng'],
    'Đắk Lắk': ['Đăk Lăk', 'Phú Yên'],
    'Điện Biên': ['Điện Biên'],
    'Đồng Nai': ['Đồng Nai', 'Bình Phước'],
    'Đồng Tháp': ['Tiền Giang', 'Đồng Tháp'],
    'Gia Lai': ['Gia Lai', 'Bình Định'],
    'Hà Tĩnh': ['Hà Tĩnh'],
    'TP Hải Phòng': ['Hải Dương', 'Hải Phòng'],
    'Hưng Yên': ['Hưng Yên', 'Thái Bình'],
    'Khánh Hoà': ['Ninh Thuận', 'Khánh Hòa'],
    'Lai Châu': ['Lai Châu'],
    'Lâm Đồng': ['Lâm Đồng', 'Đăk Nông', 'Bình Thuận'],
    'Lạng Sơn': ['Lạng Sơn'],
    'Lào Cai': ['Lào Cai', 'Yên Bái'],
    'Nghệ An': ['Nghệ An'],
    'Ninh Bình': ['Hà Nam', 'Ninh Bình', 'Nam Định'],
    'Phú Thọ': ['Vĩnh Phúc', 'Phú Thọ', 'Hòa Bình'],
    'Quảng Ngãi': ['Kon Tum', 'Quảng Ngãi'],
    'Quảng Ninh': ['Quảng Ninh'],
    'Quảng Trị': ['Quản Bình', 'Quảng Trị'],
    'Sơn La': ['Sơn La'],
    'Tây Ninh': ['Tây Ninh', 'Long An'],
    'Thái Nguyên': ['Bắc Kạn', 'Thái Nguyên'],
    'Thanh Hoá': ['Thanh Hóa'],
    'TP Hà Nội': ['Hà Nội'],
    'TP HCM': ['Bà Rịa -Vũng Tàu', 'Bình Dương', 'TP. Hồ Chí Minh'],
    'TP Huế': ['Thừa Thiên Huế'],
    'Tuyên Quang': ['Tuyên Quang', 'Hà Giang'],
    'Vĩnh Long': ['Bến Tre', 'Vĩnh Long', 'Trà Vinh']
}

# Read the KML file
def read_kml_to_geodataframe(kml_file):
    # Parse KML using pykml
    with open(kml_file, 'r', encoding='utf-8') as f:
        kml_str = f.read()
    parser = etree.XMLParser()
    kml_root = etree.fromstring(kml_str.encode('utf-8'), parser)
    
    # Extract placemarks
    placemarks = kml_root.findall('.//{http://www.opengis.net/kml/2.2}Placemark')
    data = []
    
    for placemark in placemarks:
        # Extract attributes
        gid = placemark.find('.//{http://www.opengis.net/kml/2.2}SimpleData[@name="gid"]').text
        code = placemark.find('.//{http://www.opengis.net/kml/2.2}SimpleData[@name="code"]').text
        ten_tinh = placemark.find('.//{http://www.opengis.net/kml/2.2}SimpleData[@name="ten_tinh"]').text
        
        # Extract coordinates
        polygons = []
        multi_geometries = placemark.findall('.//{http://www.opengis.net/kml/2.2}MultiGeometry')
        for multi_geom in multi_geometries:
            for polygon in multi_geom.findall('.//{http://www.opengis.net/kml/2.2}Polygon'):
                coords_str = polygon.find('.//{http://www.opengis.net/kml/2.2}coordinates').text.strip()
                coord_list = []
                for coord in coords_str.split():
                    lon, lat = map(float, coord.split(',')[:2])
                    coord_list.append((lon, lat))
                polygons.append(Polygon(coord_list))
        
        geometry = MultiPolygon(polygons) if len(polygons) > 1 else polygons[0]
        data.append({'gid': gid, 'code': code, 'ten_tinh': ten_tinh, 'geometry': geometry})
    
    # Create GeoDataFrame
    gdf = gpd.GeoDataFrame(data, geometry='geometry', crs='EPSG:4326')
    return gdf

# Map old provinces to new provinces
def map_provinces(gdf, mapping_table):
    # Create a reverse mapping: old province -> new province
    reverse_mapping = {}
    for new_prov, old_provs in mapping_table.items():
        for old_prov in old_provs:
            reverse_mapping[old_prov] = new_prov
    
    # Add new province column
    gdf['new_tinh'] = gdf['ten_tinh'].map(reverse_mapping)
    
    # Check for unmapped provinces
    unmapped = gdf[gdf['new_tinh'].isna()]
    if not unmapped.empty:
        print("Warning: The following provinces were not mapped:", unmapped['ten_tinh'].tolist())
    
    return gdf

# Merge geometries and dissolve internal boundaries
def merge_provinces(gdf):
    # Dissolve geometries by new_tinh, merging polygons and removing internal boundaries
    merged_gdf = gdf.dissolve(by='new_tinh', aggfunc={'code': 'first', 'gid': 'first'}).reset_index()
    
    # Ensure geometries are valid
    merged_gdf['geometry'] = merged_gdf['geometry'].apply(lambda geom: geom.buffer(0) if not geom.is_valid else geom)
    
    return merged_gdf

# Write new KML file
def write_kml(gdf, output_file):
    # Create KML structure
    kml = KML.kml(
        KML.Document(
            KML.Schema(
                KML.SimpleField(name="gid", type="int"),
                KML.SimpleField(name="code", type="string"),
                KML.SimpleField(name="ten_tinh", type="string"),
                name="diaphantinh_vn",
                id="diaphantinh_vn"
            ),
            KML.Folder(
                KML.name("diaphantinh_vn")
            )
        )
    )
    
    folder = kml.Document.Folder
    
    # Add placemarks
    for _, row in gdf.iterrows():
        placemark = KML.Placemark(
            KML.Style(
                KML.LineStyle(KML.color("ff0000ff")),
                KML.PolyStyle(KML.fill("0"))
            ),
            KML.ExtendedData(
                KML.SchemaData(
                    KML.SimpleData(row['gid'], name="gid"),
                    KML.SimpleData(row['code'], name="code"),
                    KML.SimpleData(row['new_tinh'], name="ten_tinh"),
                    schemaUrl="#diaphantinh_vn"
                )
            )
        )
        
        # Handle geometry
        geom = row['geometry']
        if geom.geom_type == 'Polygon':
            geom = [geom]
        elif geom.geom_type == 'MultiPolygon':
            geom = geom.geoms
        
        multi_geom = KML.MultiGeometry()
        for poly in geom:
            coords = " ".join([f"{x},{y}" for x, y in poly.exterior.coords])
            polygon = KML.Polygon(
                KML.altitudeMode("clampToGround"),
                KML.outerBoundaryIs(
                    KML.LinearRing(
                        KML.altitudeMode("clampToGround"),
                        KML.coordinates(coords)
                    )
                )
            )
            multi_geom.append(polygon)
        
        placemark.append(multi_geom)
        folder.append(placemark)
    
    # Write to file
    with open(output_file, 'wb') as f:
        f.write(etree.tostring(kml, pretty_print=True, encoding='UTF-8', xml_declaration=True))

def main():
    input_kml = 'diaphantinhvn.kml'
    output_kml = 'diaphantinhvn_merged.kml'
    
    # Read and process KML
    gdf = read_kml_to_geodataframe(input_kml)
    
    # Map provinces
    gdf = map_provinces(gdf, mapping_table)
    
    # Merge provinces
    merged_gdf = merge_provinces(gdf)
    
    # Write new KML
    write_kml(merged_gdf, output_kml)
    print(f"New KML file with {len(merged_gdf)} provinces written to {output_kml}")

if __name__ == "__main__":
    main()