import pygame
import os
import glob
import threading
import time  # Import time for the timer
import sys



# added to figure out delay
with open("/tmp/pygame_debug.log", "a") as log:
    log.write(f"[DEBUG] Script started at {time.time():.2f}\n")
    log.flush()
start_time = time.time()
with open("/tmp/pygame_debug.log", "a") as log:
    log.write(f"[DEBUG] Script started at {start_time:.2f}\n")
    log.flush()

# Optimize Pygame Display
os.environ["SDL_VIDEODRIVER"] = "wayland"  # Use "x11" if Wayland fails

# Initialize Pygame
pygame.init()
# added to figure out delay
with open("/tmp/pygame_debug.log", "a") as log:
    log.write(f"[DEBUG] Pygame initialized at {time.time() - start_time:.2f} seconds\n")
    log.flush()

# Get Screen Size
SCREEN_WIDTH = pygame.display.Info().current_w
SCREEN_HEIGHT = pygame.display.Info().current_h

# Constants
BARS = 256
MAX_BAR_HEIGHT = (SCREEN_HEIGHT // 1.1) - 32
LINE_COLOR = (0, 255, 0)  # Green Line
LINE_COLOR = (255, 255, 0)  # Yellow Line
LINE_THICKNESS = 5
SWITCH_TIMEOUT = 20  # 20 seconds timer

# Setup Pygame Display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
# added to figure out delay
with open("/tmp/pygame_debug.log", "a") as log:
    log.write(f"[DEBUG] Display initialized at {time.time() - start_time:.2f} seconds\n")
    log.flush()

# Load and Pre-Scale Background Images
background_folder = "/home/pi/Projects/cava-pygame/backgrounds"
background_images = sorted(glob.glob(os.path.join(background_folder, "*.png")))

if not background_images:
    raise FileNotFoundError("No background images found in 'backgrounds/' folder!")

backgrounds = [pygame.transform.scale(pygame.image.load(img), (SCREEN_WIDTH, SCREEN_HEIGHT)) for img in background_images]
bg_index = 0  # Start with the first background
last_switch_time = time.time()  # Timer to track background change

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
                    cava_data = data[:-158] if len(data) > 158 else data

# Start CAVA Reader Thread
cava_thread = threading.Thread(target=read_cava_data, daemon=True)
cava_thread.start()

# Main Loop
clock = pygame.time.Clock()
running = True

with open("/tmp/pygame_debug.log", "a") as log:
    log.write(f"[DEBUG] Entering main loop at {time.time() - start_time:.2f} seconds\n")
    log.flush()
while running:
    # Check if background is 2 or 3 and auto-switch back after timeout
    if bg_index in [1, 2] and time.time() - last_switch_time > SWITCH_TIMEOUT:
        bg_index = 0  # Switch back to background 1
        last_switch_time = time.time()  # Reset timer

    # Draw Background
    screen.blit(backgrounds[bg_index], (0, 0))

    # Only render visualization if background 1 is active
    if bg_index == 0:
        # Get Latest CAVA Data
        with data_lock:
            local_cava_data = cava_data[:]

        # Adjust Data Size
        BARS = len(local_cava_data)
        POINT_SPACING = SCREEN_WIDTH / (BARS - 1)

        # Normalize Values for Upper Waveform
        center_y = SCREEN_HEIGHT // 2
        upper_wave = [
            (i * POINT_SPACING, center_y - max(2, min(val, MAX_BAR_HEIGHT)) // 2)
            for i, val in enumerate(local_cava_data)
        ]

        # Create Mirrored Waveform Below
        lower_wave = [(x, 2 * center_y - y) for x, y in upper_wave]

        # Draw Thick Lines
        if len(upper_wave) > 1:
            pygame.draw.lines(screen, LINE_COLOR, False, upper_wave, LINE_THICKNESS)
            pygame.draw.lines(screen, LINE_COLOR, False, lower_wave, LINE_THICKNESS)

    # Event Handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and pygame.K_1 <= event.key <= pygame.K_9:
            key_number = event.key - pygame.K_1
            if key_number < len(backgrounds):
                bg_index = key_number  # Switch background
                last_switch_time = time.time()  # Reset timer when user switches
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False

    # Update Display
    pygame.display.flip()

    # Limit Frame Rate
    clock.tick(60)

pygame.quit()
sys.exit()