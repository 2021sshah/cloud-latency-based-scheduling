import requests
from PIL import Image
import io
import moondream as md

# Function to download an image from a URL
def download_image(image_url):
    print(f"Downloading image from {image_url}...")
    response = requests.get(image_url)
    if response.status_code == 200:
        print(f"Successfully downloaded image from {image_url}")
        return Image.open(io.BytesIO(response.content))
    else:
        print(f"Failed to download image from {image_url}")
        return None

# Function to generate captions for an image
def generate_caption(image):
    print("Loading the VL model...")
    model = md.VL("moondream-latest-int4.bin")  # Using int4.bin weights
    print("VL model loaded successfully.")
    
    # Optional: encode the image
    print("Encoding the image...")
    encoded_image = model.encode_image(image)
    print("Image encoded successfully.")
    
    # Generate caption
    print("Generating caption...")
    # caption = model.caption(encoded_image)
    for t in model.caption(encoded_image, stream=True)["caption"]:
        print(t, end="", flush=True)

    print("Caption generated successfully.")
    return "placeholder"
    
    # Return caption as a single string
    return ' '.join([line.strip() for line in caption["caption"]])

# List of image URLs and their expected captions (for comparison purposes)
image_urls = [
    "http://images.cocodataset.org/val2017/000000397133.jpg",  # Row 1
    "http://images.cocodataset.org/val2017/000000037777.jpg",  # Row 2
    "http://images.cocodataset.org/val2017/000000252219.jpg",  # Row 3
    "http://images.cocodataset.org/val2017/000000087038.jpg",  # Row 4
    "http://images.cocodataset.org/val2017/000000174482.jpg"   # Row 5
]

# Expected captions (for reference)
expected_captions = [
    "A man is in a kitchen making pizzas.",
    "The dining table near the kitchen has a bowl of fruit on it.",
    "a person with a shopping cart on a city street",
    "A person on a skateboard and bike at a skate park.",
    "a blue bike parked on a side walk"
]

# Open file to save captions
with open("sample_captions.txt", "w") as f:
    for i, url in enumerate(image_urls):
        print(f"Processing image {i+1} from {url}")
        
        # Download image
        image = download_image(url)
        
        if image:
            # Generate caption for the image
            caption = generate_caption(image)
            
            # Print and save caption
            print(f"Generated caption for image {i+1}: {caption}\n")
            f.write(f"Image {i+1} ({url}): {caption}\n")
            f.write(f"Expected caption: {expected_captions[i]}\n\n")
