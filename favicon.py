from PIL import Image

# Open the image file
img_path = r'C:\Users\user\OneDrive\Desktop\static\Favicons\Blue.png'
img = Image.open(img_path)

# Resize the image to the correct size for a favicon (64x64)
favicon_size = (64, 64)
img = img.resize(favicon_size, Image.LANCZOS)

# Save the image as an .ico file
favicon_path = 'favicon.ico'
img.save(favicon_path, format='ICO')
