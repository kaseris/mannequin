import ezdxf


def extract_coordinates(dxf_path):
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()

    coordinates = []

    for entity in msp:
        if entity.dxftype() == 'POLYLINE':
            for vertex in entity.vertices:
                coordinates.append((vertex.dxf.location[0], vertex.dxf.location[1], vertex.dxf.location[2]))
        elif entity.dxftype() == 'LINE':
            coordinates.append((entity.dxf.start[0], entity.dxf.start[1], entity.dxf.start[2]))
            coordinates.append((entity.dxf.end[0], entity.dxf.end[1], entity.dxf.end[2]))

    return coordinates


dxf_path = "/home/aboumpakis/Desktop/DXF_convert_doulevei xwris kampiles/cloth_pattern.dxf"
output_file_path = "/home/aboumpakis/Desktop/DXF_convert_doulevei xwris kampiles/coordinates.xyz"

# Extract the coordinates from the DXF file
coordinates = extract_coordinates(dxf_path)

# Delete duplicates
filtered_coordinates = []
prev_coord = None

for coord in coordinates:
    if coord != prev_coord:
        filtered_coordinates.append(coord)
        prev_coord = coord

coordinates = filtered_coordinates

# Write the coordinates to the output file
with open(output_file_path, "w") as output_file:
    for coordinate in coordinates:
        x, y, z = coordinate
        output_file.write(f"{x},0.0,{y}\n")


def create_dxf_file(input_filename, output_filename):
    with open(input_filename, 'r') as xyz_file:
        lines = xyz_file.readlines()

    # Extract x, z, and y coordinates from each line
    coordinates = [(float(line.strip().split(',')[0]), 0.0, float(line.strip().split(',')[2])) for line in lines]

    # Open the output DXF file for writing
    with open(output_filename, 'w') as dxf_file:
        # DXF header section
        dxf_file.write("0\nSECTION\n")
        dxf_file.write("2\nHEADER\n")
        dxf_file.write("9\n$ACADVER\n1\nAC1009\n")
        #         dxf_file.write("9\n$EXTMIN\n10\n-100.000\n20\n-100.000\n")
        #         dxf_file.write("9\n$EXTMAX\n10\n100.000\n20\n100.000\n")
        dxf_file.write("0\nENDSEC\n")

        # DXF entities section
        dxf_file.write("0\nSECTION\n")
        dxf_file.write("2\nTABLES\n")
        dxf_file.write("0\nENDSEC\n")
        dxf_file.write("0\nSECTION\n")

        dxf_file.write("2\nBLOCKS\n")

        dxf_file.write("0\nBLOCK\n")
        dxf_file.write("8\n1\n")
        dxf_file.write("2\nBLOCK_1\n")
        dxf_file.write("10\n0.0000\n")
        dxf_file.write("20\n0.0000\n")
        dxf_file.write("70\n0\n")

        # POLYLINE entity
        dxf_file.write("0\nPOLYLINE\n")
        dxf_file.write("8\n0\n")
        dxf_file.write("66\n1\n")
        dxf_file.write("70\n0\n")

        # Create a set to store the coordinates
        seen_coordinates = set()

        s = []
        # VERTEX entities for each coordinate
        for i, coordinate in enumerate(coordinates):
            dxf_file.write("0\nVERTEX\n")
            dxf_file.write("8\n0\n")
            dxf_file.write(f"10\n{coordinate[0]}\n")
            dxf_file.write(f"20\n{coordinate[2]}\n")
            dxf_file.write(f"30\n{coordinate[1]}\n")

            if (coordinate[0], coordinate[1], coordinate[2]) in seen_coordinates:
                s.append(i)
                if i + 1 == len(coordinates):
                    dxf_file.write("0\nSEQEND\n")
                    dxf_file.write("0\nENDBLK\n")
                    dxf_file.write("0\nENDSEC\n")
                    dxf_file.write("0\nSECTION\n")
                    dxf_file.write("2\nENTITIES\n")
                    dxf_file.write("0\nINSERT\n")
                    dxf_file.write("8\n1\n")
                    dxf_file.write("2\nBLOCK_1\n")
                    dxf_file.write("10\n0\n")
                    dxf_file.write("20\n0\n")
                else:
                    dxf_file.write("0\nSEQEND\n")
                    dxf_file.write("0\nENDBLK\n")
                    dxf_file.write("0\nBLOCK\n")
                    dxf_file.write("8\n1\n")
                    dxf_file.write("2\nBLOCK_" + str(i) + "\n")
                    dxf_file.write("10\n0.0000\n")
                    dxf_file.write("20\n0.0000\n")
                    dxf_file.write("70\n0\n")

                    # POLYLINE entity
                    dxf_file.write("0\nPOLYLINE\n")
                    dxf_file.write("8\n0\n")
                    dxf_file.write("66\n1\n")
                    dxf_file.write("70\n0\n")

                    # Add the coordinate to the set
            seen_coordinates.add((coordinate[0], coordinate[1], coordinate[2]))

        for j in range(0, len(s) - 1):
            dxf_file.write("0\nINSERT\n")
            dxf_file.write("8\n1\n")
            dxf_file.write("2\nBLOCK_" + str(s[j]) + "\n")
            dxf_file.write("10\n0\n")
            dxf_file.write("20\n0\n")

        # Close the DXF entities section
        dxf_file.write("0\nENDSEC\n")

        # EOF tag
        dxf_file.write("0\nEOF\n")


create_dxf_file("/home/aboumpakis/Desktop/DXF_convert_doulevei xwris kampiles/coordinates.xyz",
                "/home/aboumpakis/Desktop/DXF_convert_doulevei xwris kampiles/dxf_AAMA_final.dxf")