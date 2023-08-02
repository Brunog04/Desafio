import pandas as pd
import re
import geopandas as gpd
from shapely.geometry import Polygon
import os
import matplotlib.pyplot as plt

def read_data_file(file_path: str) -> pd.DataFrame:
    with open(file_path, 'r') as f:
        raw_file = f.readlines()

    list_dados = [line.split() for line in raw_file]
    float_raw_lines = [list(map(float, raw_line)) for raw_line in list_dados]
    return pd.DataFrame(float_raw_lines, columns=['lat', 'long', 'data_value'])

def read_contour_file(file_path: str) -> pd.DataFrame:
    line_split_comp = re.compile(r'\s*,')

    with open(file_path, 'r') as f:
        raw_file = f.readlines()

    l_raw_lines = [line_split_comp.split(raw_file_line.strip()) for raw_file_line in raw_file]
    l_raw_lines = list(filter(lambda item: bool(item[0]), l_raw_lines))
    float_raw_lines = [list(map(float, raw_line))[:2] for raw_line in l_raw_lines]
    header_line = float_raw_lines.pop(0)
    assert len(float_raw_lines) == int(header_line[0])
    return pd.DataFrame(float_raw_lines, columns=['lat', 'long'])

def apply_contour(contour_df: pd.DataFrame, data_df: pd.DataFrame) -> int:
    #Aplica o contorno ao DataFrame de dados e retorna a soma das previsões.
    coord = list(zip(contour_df['long'], contour_df['lat']))
    polygon = Polygon(coord)
    gdf_polygon = gpd.GeoDataFrame({'geometry': [polygon]})
    data_df['geometry'] = gpd.points_from_xy(data_df['long'], data_df['lat'])
    gdf_points = gpd.GeoDataFrame(data_df, geometry='geometry')
    filter_points = gdf_points.drop(columns=['geometry','lat','long'])[gdf_points.within(gdf_polygon.geometry.iloc[0])]
    data_value_sum = filter_points['data_value'].sum()
    return data_value_sum

def plot_grafico(total_points: pd.DataFrame):
    #Plota um gráfico de previsão de precipitação.
    x = total_points['forecasted_date'].astype(str)
    y = total_points['data_value']
    plt.bar(x, y)
    for index, row in total_points.iterrows():
        value = "{:.2f}".format(row['data_value'])
        plt.text(index, row['data_value'], value, ha='center', va='bottom')
    plt.xlabel('Dia Previsto')
    plt.ylabel('Previsão de Precipitação Acumulada (mm)')
    plt.title('Previsão de Precipitação Acumulada para a Região de Camargos')
    plt.xticks(rotation=40, ha='right')
    plt.tight_layout()
    plt.show()

def main() -> pd.DataFrame:
    #Função principal para processar os dados e gerar o gráfico.
    data_folder = 'btg-energy-challenge/forecast_files'
    list_arquivos = os.listdir(data_folder)
    len_arquivos = sum(1 for arquivo in list_arquivos if arquivo.endswith('.dat'))
    
    day = int(list_arquivos[0][14:16])
    total_points = pd.DataFrame(columns=['forecast_date', 'forecasted_date', 'data_value'])
    
    for i in range(len_arquivos):
        data_file = f"ETA40_p011221a{day}1221.dat" if day > 9 else f"ETA40_p011221a0{day}1221.dat"
        contour_df = read_contour_file('btg-energy-challenge/PSATCMG_CAMARGOS.bln')
        data_df = read_data_file(os.path.join(data_folder, data_file))
        forecast_date = f"{list_arquivos[i][7:9]}/{list_arquivos[i][9:11]}/{list_arquivos[i][11:13]}"
        forecasted_date = f"{list_arquivos[i][14:16]}/{list_arquivos[i][16:18]}/{list_arquivos[i][18:20]}"
        precipitacao = apply_contour(contour_df=contour_df, data_df=data_df)
        total_points = total_points.append({'data_value': precipitacao,
                                            'forecast_date': forecast_date,
                                            'forecasted_date': forecasted_date,
                                           }, ignore_index=True)
        day += 1
    
    return total_points

if __name__ == '__main__':
    total_points = main()
    plot_grafico(total_points)