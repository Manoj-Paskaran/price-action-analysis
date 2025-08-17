import pandas as pd

def loader():
    data = []
    for file_name in ['Advertising_Agencies.csv', 'Aerospace_&_Defense.csv', 'Agricultural_Inputs.csv',
                      'Airlines.csv', 'Airports_&_Air_Services.csv', 'Aluminum.csv', 'Auto_Manufacturers.csv',
                      'Auto_Parts.csv', 'Auto_&_Truck_Dealerships.csv', 'Apparel_Retail.csv', 'Apparel_Manufacturing.csv']:
        path = f'data//{file_name}'
        dt = pd.read_csv(path)
        data.append(dt)

    return pd.concat(data)


if __name__ == '__main__':
    data = loader()
    print(data)