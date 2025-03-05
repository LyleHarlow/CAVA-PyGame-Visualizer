import pygame
import os
import glob

# Setup
WIDTH, HEIGHT = 800, 400
BARS = 60  # Number of bars to display
BAR_WIDTH = WIDTH // BARS

# Colors
BAR_COLOR = (0, 255, 0)  # Green bars

# Initialize pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("CAVA Visualization Overlay")

# Load multiple background images from a folder
background_folder = "backgrounds"  # Folder where images are stored
background_images = sorted(glob.glob(os.path.join(background_folder, "*.png")))  # Load all PNG images
if not background_images:
    raise FileNotFoundError("No background images found in 'backgrounds/' folder!")

# Function to load and scale the background image
def load_background(index):
    if 0 <= index < len(background_images):
        image = pygame.image.load(background_images[index])
        return pygame.transform.scale(image, (WIDTH, HEIGHT))
    return None

# Load first background
bg_index = 0
background = load_background(bg_index)

# Open FIFO for reading CAVA data
fifo_path = "/tmp/cava.fifo"
if not os.path.exists(fifo_path):
    os.mkfifo(fifo_path)

# Function to read CAVA data
def read_cava_data():
    with open(fifo_path, "r") as fifo:
        while True:
            data = fifo.readline().strip()
            if data:
                yield list(map(int, data.split()))

# Start reading CAVA data
cava_data_gen = read_cava_data()

running = True
while running:
    screen.blit(background, (0, 0))  # Draw current background

    # Read and process CAVA data
    try:
        cava_data = next(cava_data_gen)
        if len(cava_data) != BARS:
            cava_data = [0] * BARS  # Reset if data length is incorrect
    except StopIteration:
        cava_data = [0] * BARS

    # Draw bars
    for i in range(BARS):
        bar_height = cava_data[i] * 2  # Scale bar height
        pygame.draw.rect(screen, BAR_COLOR, (i * BAR_WIDTH, HEIGHT - bar_height, BAR_WIDTH - 2, bar_height))

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if pygame.K_1 <= event.key <= pygame.K_9:  # Key '1' to '9'
                key_number = event.key - pygame.K_1  # Convert key to index (0-based)
                if key_number < len(background_images):  # Check if valid background index
                    bg_index = key_number
                    background = load_background(bg_index)

    pygame.display.flip()  # Update screen
    pygame.time.delay(16)  # 60 FPS cap

pygame.quit()
