import pygame
import os
import glob
import threading

# Optimize Pygame Display
os.environ["SDL_VIDEODRIVER"] = "wayland"  # Use "x11" if Wayland fails

# Initialize Pygame
pygame.init()

# Get Screen Size
SCREEN_WIDTH = pygame.display.Info().current_w
SCREEN_HEIGHT = pygame.display.Info().current_h

# Constants
BARS = 256  # Acts as the number of points in the line graph
SPACING = 1
MAX_BAR_HEIGHT = (SCREEN_HEIGHT // 2) - 32  # Half-screen for mirroring
LINE_COLOR = (0, 255, 0)  # Green Line

# Setup Pygame Display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)

# Load and Pre-Scale Background Images
background_folder = "/home/pi/Projects/cava-pygame/backgrounds"
background_images = sorted(glob.glob(os.path.join(background_folder, "*.png")))

if not background_images:
    raise FileNotFoundError("No background images found in 'backgrounds/' folder!")

backgrounds = [pygame.transform.scale(pygame.image.load(img), (SCREEN_WIDTH, SCREEN_HEIGHT)) for img in background_images]
bg_index = 0

# Open FIFO for CAVA Data
fifo_path = "/tmp/cava.fifo"
if not os.path.exists(fifo_path):
    os.mkfifo(fifo_path)

# Shared Data Storage
cava_data = [0] * BARS
data_lock = threading.Lock()

# Non-Blocking CAVA Data Reader
def read_cava_data():
    global cava_data
    with open(fifo_path, "r") as fifo:
        for line in fifo:
            data = [int(x) for x in line.strip().split(";") if x.strip().isdigit()]
            if data:
                with data_lock:
                    cava_data = data[:-158] if len(data) > 158 else data  # Trim data

# Start CAVA Reader Thread
cava_thread = threading.Thread(target=read_cava_data, daemon=True)
cava_thread.start()

# Main Loop
clock = pygame.time.Clock()
running = True

while running:
    # Draw Background
    screen.blit(backgrounds[bg_index], (0, 0))

    # Get Latest CAVA Data
    with data_lock:
        local_cava_data = cava_data[:]

    # Adjust Data Size
    BARS = len(local_cava_data)
    POINT_SPACING = SCREEN_WIDTH / (BARS - 1)  # Evenly space points

    # Normalize Values for Upper Waveform
    center_y = SCREEN_HEIGHT // 2
    upper_wave = [
        (i * POINT_SPACING, center_y - max(2, min(val, MAX_BAR_HEIGHT)) // 2)
        for i, val in enumerate(local_cava_data)
    ]

    # Create Mirrored Waveform Below
    lower_wave = [
        (x, 2 * center_y - y) for x, y in upper_wave
    ]

    # Draw Upper and Lower Waveforms
    if len(upper_wave) > 1:
        pygame.draw.aalines(screen, LINE_COLOR, False, upper_wave, 1)
        pygame.draw.aalines(screen, LINE_COLOR, False, lower_wave, 1)

    # Event Handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and pygame.K_1 <= event.key <= pygame.K_9:
            key_number = event.key - pygame.K_1
            if key_number < len(backgrounds):
                bg_index = key_number

    # Update Display
    pygame.display.flip()

    # Limit Frame Rate
    clock.tick(60)

pygame.quit()
