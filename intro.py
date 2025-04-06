import pygame
import os
import glob
import threading
import time
import sys

# Debugging - Log startup times
debug_log = "/tmp/pygame_debug.log"
with open(debug_log, "a") as log:
    start_time = time.time()
    log.write(f"[DEBUG] Script started at {start_time:.2f}\n")
    log.flush()

# Optimize Pygame Display
os.environ["SDL_VIDEODRIVER"] = "wayland"

# Initialize Pygame
pygame.init()
with open(debug_log, "a") as log:
    log.write(f"[DEBUG] Pygame initialized at {time.time() - start_time:.2f} seconds\n")
    log.flush()

# Get Screen Size
SCREEN_WIDTH = pygame.display.Info().current_w
SCREEN_HEIGHT = pygame.display.Info().current_h

# Constants
BARS = 256
MAX_BAR_HEIGHT = (SCREEN_HEIGHT // 1.1) - 32
LINE_COLOR = (255, 255, 0)  # Yellow Line
LINE_THICKNESS = 5
SWITCH_TIMEOUT = 20  # 20 seconds for auto-switching backgrounds

# Setup Pygame Display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)

# Debugging log
with open(debug_log, "a") as log:
    log.write(f"[DEBUG] Display initialized at {time.time() - start_time:.2f} seconds\n")
    log.flush()

# Load and Pre-Scale Background Images
background_folder = "/home/pi/Projects/cava-pygame/backgrounds"
background_images = sorted(glob.glob(os.path.join(background_folder, "*.png")))

if not background_images:
    raise FileNotFoundError("No background images found in 'backgrounds/' folder!")

backgrounds = [pygame.transform.scale(pygame.image.load(img), (SCREEN_WIDTH, SCREEN_HEIGHT)) for img in background_images]
bg_index = 0  # Start with the first background
last_switch_time = time.time()  # Timer for background switching

# Open FIFO for CAVA Data
fifo_path = "/tmp/cava.fifo"
if not os.path.exists(fifo_path):
    os.mkfifo(fifo_path)

# Shared Data Storage
cava_data = [0] * BARS
data_lock = threading.Lock()

# Scaling function for CAVA data
def scale_cava_output(bars, max_height=MAX_BAR_HEIGHT):
    """ Dynamically scales the audio data to fit within the visualization range. """
    max_value = max(bars) if max(bars) > 0 else 1  # Avoid division by zero
    scale_factor = max_height / max_value  # Precompute scale factor
    return [int(bar * scale_factor) for bar in bars]  # Apply scaling

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

# Debugging log
with open(debug_log, "a") as log:
    log.write(f"[DEBUG] Entering main loop at {time.time() - start_time:.2f} seconds\n")
    log.flush()

while running:
    # Auto-switch background after timeout
    if bg_index in [1, 2] and time.time() - last_switch_time > SWITCH_TIMEOUT:
        bg_index = 0  # Reset to default background
        last_switch_time = time.time()

    # Draw Background
    screen.blit(backgrounds[bg_index], (0, 0))

    # Render visualization only when background 1 is active
    if bg_index == 0:
        # Get Latest CAVA Data
        with data_lock:
            local_cava_data = cava_data[:]

        # Normalize CAVA data
        scaled_bars = scale_cava_output(local_cava_data)

        # Adjust Data Size
        BARS = len(scaled_bars)
        POINT_SPACING = SCREEN_WIDTH / (BARS - 1)
        center_y = SCREEN_HEIGHT // 2

        # Generate waveform points
        upper_wave = [(i * POINT_SPACING, center_y - max(2, min(val, MAX_BAR_HEIGHT)) // 2) for i, val in enumerate(scaled_bars)]
        lower_wave = [(x, 2 * center_y - y) for x, y in upper_wave]

        # Draw waveforms
        if len(upper_wave) > 1:
            pygame.draw.lines(screen, LINE_COLOR, False, upper_wave, LINE_THICKNESS)
            pygame.draw.lines(screen, LINE_COLOR, False, lower_wave, LINE_THICKNESS)

    # Event Handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if pygame.K_1 <= event.key <= pygame.K_9:
                key_number = event.key - pygame.K_1
                if key_number < len(backgrounds):
                    bg_index = key_number  # Change background
                    last_switch_time = time.time()
            elif event.key == pygame.K_ESCAPE:
                running = False

    # Update Display
    pygame.display.flip()

    # Limit Frame Rate
    clock.tick(60)

pygame.quit()
sys.exit()
