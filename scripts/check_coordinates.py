import csv

print("\n🔍 Verificando cidades suspeitas mencionadas:\n")
print("="*100)

suspeitas = ['Astrakhan', 'Hampton', 'Nghi Son', 'Quang Yen', 'Jiaxing', 'Metairie']

with open('data/csv/worldcities.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['city'] in suspeitas:
            lat = row['lat']
            lng = row['lng']
            status = "✅ OK" if '.' in lat and '.' in lng else "❌ SEM PONTO"
            print(f"{status} | {row['city']:20s} | {row['country']:20s} | lat={lat:10s} | lng={lng:10s}")
