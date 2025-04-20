import geopandas as gpd
import pandas as pd
from uuid import uuid4

# Define the mapping table as a dictionary
province_mapping = {
    'An Giang': 'An Giang',
    'Kien Giang': 'An Giang',
    'Bắc Giang': 'Bắc Ninh',
    'Bắc Ninh': 'Bắc Ninh',
    'Bạc Liêu': 'Cà Mau',
    'Cà Mau': 'Cà Mau',
    'Cao Bằng': 'Cao Bằng',
    'Đăk Lăk': 'Đắk Lắk',
    'Phú Yên': 'Đắk Lắk',
    'Điện Biên': 'Điện Biên',
    'Bình Phước': 'Đồng Nai',
    'Đồng Nai': 'Đồng Nai',
    'Đồng Tháp': 'Đồng Tháp',
    'Tiền Giang': 'Đồng Tháp',
    'Bình Định': 'Gia Lai',
    'Gia Lai': 'Gia Lai',
    'Hà Tĩnh': 'Hà Tĩnh',
    'Hưng Yên': 'Hưng Yên',
    'Thái Bình': 'Hưng Yên',
    'Khánh Hòa': 'Khánh Hoà',
    'Ninh Thuận': 'Khánh Hoà',
    'Lai Châu': 'Lai Châu',
    'Bình Thuận': 'Lâm Đồng',
    'Đăk Nông': 'Lâm Đồng',
    'Lâm Đồng': 'Lâm Đồng',
    'Lạng Sơn': 'Lạng Sơn',
    'Lào Cai': 'Lào Cai',
    'Yên Bái': 'Lào Cai',
    'Nghệ An': 'Nghệ An',
    'Hà Nam': 'Ninh Bình',
    'Nam Định': 'Ninh Bình',
    'Ninh Bình': 'Ninh Bình',
    'Hòa Bình': 'Phú Thọ',
    'Phú Thọ': 'Phú Thọ',
    'Vĩnh Phúc': 'Phú Thọ',
    'Kon Tum': 'Quảng Ngãi',
    'Quảng Ngãi': 'Quảng Ngãi',
    'Quảng Ninh': 'Quảng Ninh',
    'Quản Bình': 'Quảng Trị',
    'Quảng Trị': 'Quảng Trị',
    'Sơn La': 'Sơn La',
    'Long An': 'Tây Ninh',
    'Tây Ninh': 'Tây Ninh',
    'Bắc Kạn': 'Thái Nguyên',
    'Thái Nguyên': 'Thái Nguyên',
    'Thanh Hóa': 'Thanh Hoá',
    'Hậu Giang': 'TP Cần Thơ',
    'Sóc Trăng': 'TP Cần Thơ',
    'Cần Thơn': 'TP Cần Thơ',
    'Quảng Nam': 'TP Đà Nẵng',
    'Đà Nẵng': 'TP Đà Nẵng',
    'Hà Nội': 'TP Hà Nội',
    'Hải Dương': 'TP Hải Phòng',
    'Hải Phòng': 'TP Hải Phòng',
    'Bà Rịa -Vũng Tàu': 'TP HCM',
    'Bình Dương': 'TP HCM',
    'TP. Hồ Chí Minh': 'TP HCM',
    'Thừa Thiên Huế': 'TP Huế',
    'Hà Giang': 'Tuyên Quang',
    'Tuyên Quang': 'Tuyên Quang',
    'Bến Tre': 'Vĩnh Long',
    'Trà Vinh': 'Vĩnh Long',
    'Vĩnh Long': 'Vĩnh Long'
}

# Read the input GeoJSON file
gdf = gpd.read_file('diaphantinh.geojson', encoding='utf-8')

# Map the original province names to new province names
gdf['new_tinh'] = gdf['ten_tinh'].map(province_mapping)

# Check for unmapped provinces
unmapped = gdf[gdf['new_tinh'].isna()]['ten_tinh'].unique()
if len(unmapped) > 0:
    print(f"Warning: The following provinces were not mapped: {unmapped}")

# Dissolve geometries by new province name to merge and remove shared boundaries
gdf_dissolved = gdf.dissolve(by='new_tinh', aggfunc={
    'code': 'first',  # Keep the first code
    'gid': 'first'    # Keep the first gid
}).reset_index()

# Rename the dissolved column back to 'ten_tinh'
gdf_dissolved = gdf_dissolved.rename(columns={'new_tinh': 'ten_tinh'})

# Assign new unique gids
gdf_dissolved['gid'] = range(1, len(gdf_dissolved) + 1)

# Generate new codes in the format VNXX where XX is the two-digit gid
gdf_dissolved['code'] = gdf_dissolved['gid'].apply(lambda x: f'VN{x:02d}')

# Save the output GeoJSON file with UTF-8 encoding
gdf_dissolved.to_file('diaphantinhvn_merged.geojson', driver='GeoJSON', encoding='utf-8')

# Print confirmation
print(f"Successfully created diaphantinhvn_merged.geojson with {len(gdf_dissolved)} provinces")