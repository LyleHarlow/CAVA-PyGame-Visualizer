import pygame
import os
import glob

# Setup
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 400
BARS = 256  # Number of bars to display
BAR_WIDTH = SCREEN_WIDTH // BARS

# Colors
BAR_COLOR = (0, 255, 0)  # Green bars

# Initialize pygame
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("CAVA Visualization Overlay")

# Load multiple background images from a folder
background_folder = "/home/pi/Projects/cava-pygame/backgrounds"  # Folder where images are stored
background_images = sorted(glob.glob(os.path.join(background_folder, "*.png")))  # Load all PNG images
if not background_images:
    raise FileNotFoundError("No background images found in 'backgrounds/' folder!")

# Function to load and scale the background image
def load_background(index):
    if 0 <= index < len(background_images):
        image = pygame.image.load(background_images[index])
        return pygame.transform.scale(image, (SCREEN_WIDTH, SCREEN_HEIGHT))
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
                yield [int(x) for x in data.split(';') if x.strip().isdigit()]

# Start reading CAVA data
cava_data_gen = read_cava_data()

running = True
while running:
    screen.blit(background, (0, 0))  # Draw current background

    # Read and process CAVA data
    try:
        cava_data = next(cava_data_gen)
        chop_top = 158
        # cava_data = cava_data[:len(cava_data) // 2]  # Only first half
        cava_data = cava_data[:-chop_top]  # Remove last 20 bars
        BARS = len(cava_data) # Update BARS dynamically
        #print("BARS:", BARS)  # Debugging output
        BAR_WIDTH = (SCREEN_WIDTH // BARS) -1
        #print("BAR_WIDTH:", BAR_WIDTH)  # Debugging output
        #print("CAVA Data:", cava_data) #debuging line
        if len(cava_data) != BARS:
            cava_data = [0] * BARS  # Reset if data length is incorrect
    except StopIteration:
        cava_data = [0] * BARS

    ## ---- DRAW TEST BARS ---- ##
    # for i in range(10):  # Draw 10 test bars
    #     pygame.draw.rect(screen, (255, 0, 0), (i * 20, 300, 15, 100))  # Red test bars
    # print("Test bars drawn!")  # Debugging output

    # Draw CAVA bars (if data exists)
##    for i in range(BARS):
#        bar_height = cava_data[i] * 2  # Scale bar height
##        bar_height = max(10, min(cava_data[i] * 2, 350))  # Scale bar height
##        pygame.draw.rect(screen, BAR_COLOR, (i * BAR_WIDTH, HEIGHT - bar_height, BAR_WIDTH - 2, bar_height))
#     # Constants for bar sizes
    SPACING = 1

    # Calculate total width of the visualizer
    visualizer_width = (BAR_WIDTH + SPACING) * BARS - SPACING  # Remove last spacing
#    start_x = (SCREEN_WIDTH - visualizer_width) // 2  # Center horizontally
    start_x = BAR_WIDTH  # Left align

    # Maximum bar height
    MAX_BAR_HEIGHT = SCREEN_HEIGHT // 2  # Adjust based on preference

    for i, value in enumerate(cava_data):
        bar_height = max(2, min(value, MAX_BAR_HEIGHT))  # Limit bar height
        x_pos = start_x + i * (BAR_WIDTH + SPACING)  # X position stays the same

        # Center vertically: draw bars both upwards and downwards from the middle
        center_y = SCREEN_HEIGHT // 2
        y_pos = center_y - (bar_height // 2)

        # Draw the bar
        pygame.draw.rect(screen, (0, 255, 0), (x_pos, y_pos, BAR_WIDTH, bar_height))
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
#    pygame.time.delay(16)  # 60 FPS cap

pygame.quit()
