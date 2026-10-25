import datetime as dt
from PIL import Image, ImageDraw, ImageFont


def combine_images_grid(input_files, output_file, m=3, n=2):
    """
    Combines images into a single image in a mxn grid with no padding.
    Assumes all input images have the same dimensions.
    """

    images = []
    for file_path in input_files:
        try:
            img = Image.open(file_path)
            # Ensure images are in a common mode like RGB for consistent pasting
            images.append(img.convert('RGB'))
        except FileNotFoundError:
            print(f"Error: File not found at {file_path}")
            return
        except Exception as e:
            print(f"Error opening image {file_path}: {e}")
            return

    # 2. Get the dimensions of the first image (assuming uniformity)
    # We will tile them tightly, so spacing is not needed.
    img_width, img_height = images[0].size

    # Check that all images are the same size for a clean grid
    for i, img in enumerate(images[1:], start=2):
        if img.size != (img_width, img_height):
            print(f"Warning: Image {i} has different dimensions. The grid might not be perfectly tight.")

    # 3. Calculate total dimensions of the composite image
    grid_rows = m
    grid_cols = n

    total_width = img_width * grid_cols
    total_height = img_height * grid_rows

    # 4. Create a new, blank canvas for the combined image
    combined_image = Image.new('RGB', (total_width, total_height), color='white')

    # 5. Paste each image into the correct position
    # The outer loop is for rows, and the inner loop is for columns
    for row in range(grid_rows):
        for col in range(grid_cols):
            # Calculate the index of the image
            image_index = row * grid_cols + col

            # Calculate the top-left (x, y) coordinates for pasting
            x_paste = col * img_width
            y_paste = row * img_height

            # Paste the image
            combined_image.paste(images[image_index], (x_paste, y_paste))
    draw = ImageDraw.Draw(combined_image)
    # draw.text((2200, 200), "a", font_size=150, fill=(0, 0, 0))
    # draw.text((4600, 200), "b", font_size=150, fill=(0, 0, 0))
    # draw.text((2200, 3800), "c", font_size=150, fill=(0, 0, 0))
    # draw.text((4600, 3800), "d", font_size=150, fill=(0, 0, 0))
    # draw.text((2050, 2000), "Apr. 01,\n2023", font_size=120, fill=(0, 0, 0))
    # draw.text((2050, 5600), "Apr. 03,\n2023", font_size=120, fill=(0, 0, 0))
    # draw.text((1050, 60), "Ionosondes", font_size=80, fill=(0, 0, 0))
    # draw.text((3600, 60), "GNSS receivers", font_size=80, fill=(0, 0, 0))

    # 6. Save the final image
    combined_image.save(output_file)
    print(f"Successfully combined images into a tight {m}x{n} grid and saved as: {output_file}")


def combine_GNSS_figures():
    # Define the file paths for your 6 images.
    # Replace these placeholder names with your actual filenames.
    dir_1 = r"c:\Users\Sergii\Dell_D\Coding\Python\PyCharm\GNSS_Analysis\results\out\EU\2024\2024-09-08\3600\Time\Single\All\fig"
    dir_2 = r"c:\Users\Sergii\Dell_D\Coding\Python\PyCharm\GNSS_Analysis\results\out\EU\2024\2024-09-09\3600\Time\Single\All\fig"
    dir_3 = r"c:\Users\Sergii\Dell_D\Coding\Python\PyCharm\GNSS_Analysis\results\out\EU\2024\2024-09-10\3600\Time\Single\All\fig"
    dir_4 = r"c:\Users\Sergii\Dell_D\Coding\Python\PyCharm\GNSS_Analysis\results\out\EU\2024\2024-09-11\3600\Time\Single\All\fig"
    dir_5 = r"c:\Users\Sergii\Dell_D\Coding\Python\PyCharm\GNSS_Analysis\results\out\EU\2024\2024-09-12\3600\Time\Single\All\fig"
    dir_6 = r"c:\Users\Sergii\Dell_D\Coding\Python\PyCharm\GNSS_Analysis\results\out\EU\2024\2024-09-22\3600\Time\Single\All\fig"

    time_start = dt.datetime(2024, 9, 8, 8, 0, 0)
    time_end = dt.datetime(2024, 9, 8, 14, 0, 0)
    time_delta = dt.timedelta(minutes=1)
    time = time_start
    while time <= time_end:
        c_time = time.time().strftime("%H%M%S")
        fig_file = f"{c_time}_0030.png"
        image_paths = [
            f"{dir_1}\\{fig_file}", f"{dir_2}\\{fig_file}", f"{dir_3}\\{fig_file}",  # Row 1
            f"{dir_4}\\{fig_file}", f"{dir_5}\\{fig_file}", f"{dir_6}\\{fig_file}"  # Row 2
        ]

        # Define the output filename
        output_filename = f"comb/{fig_file}"

        # Call the function
        combine_images_grid(image_paths, output_filename)
        time += time_delta


# --- Main Execution ---
if __name__ == "__main__":
    # combine_GNSS_figures()
    input_images = (
        r"c:\Users\Sergii\Dell_D\MyPapers\Papar_CIR_Apr01_2023\Figures\0304\55 N, 5 W.png",
        r"c:\Users\Sergii\Dell_D\MyPapers\Papar_CIR_Apr01_2023\Figures\0304\55 N, 15 E.png",
        r"c:\Users\Sergii\Dell_D\MyPapers\Papar_CIR_Apr01_2023\Figures\0304\40 N, 5 W.png",
        r"c:\Users\Sergii\Dell_D\MyPapers\Papar_CIR_Apr01_2023\Figures\0304\40 N, 15 E.png"
    )
    input_images_1 = (
        r"c:\Users\Sergii\Dell_D\Coding\Python\PyCharm\GNSS_Analysis\ionosondes_01_04_2023.png",
        r"c:\Users\Sergii\Dell_D\Coding\Python\PyCharm\GNSS_Analysis\receivers_01_04_2023.png"
    )
    input_images_2 = (
        r"c:\Users\Sergii\Dell_D\Coding\GeoSpace\iono\JR055_PQ052_DB049_0104.png",
        r"c:\Users\Sergii\Dell_D\MyPapers\Papar_CIR_Apr01_2023\Figures\0104\52 N, 7 E.png",
        r"c:\Users\Sergii\Dell_D\Coding\GeoSpace\iono\JR055_PQ052_DB049_0304.png",
        r"c:\Users\Sergii\Dell_D\MyPapers\Papar_CIR_Apr01_2023\Figures\0304\52 N, 7 E.png"
    )
    input_images_3 = (
        r"c:\Users\Sergii\Dell_D\Coding\Python\PyCharm\HWM2\hwm_300_10423_18_30.png",
        r"c:\Users\Sergii\Dell_D\Coding\Python\PyCharm\HWM2\hwm_300_10423_20_30.png"
    )
    input_images_4 = (
        r"c:\Users\Sergii\Dell_D\Coding\Python\PyCharm\HWM2\HF-INT_010423_19_30.png",
        r"c:\Users\Sergii\Dell_D\Coding\Python\PyCharm\HWM2\HF-INT_030423_19_30.png"
    )
    output_file = "corr_comb_HF_INT.png"
    combine_images_grid(input_images_4, output_file, m=1, n=2)
