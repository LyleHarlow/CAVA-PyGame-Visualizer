import pygame
import os
import glob
import threading
import time

# Optimize Pygame Display
os.environ["SDL_VIDEODRIVER"] = "wayland"

# Initialize Pygame
pygame.init()

# Get Screen Size
SCREEN_WIDTH = pygame.display.Info().current_w
SCREEN_HEIGHT = pygame.display.Info().current_h

# Constants
BARS = 256
MAX_BAR_HEIGHT = (SCREEN_HEIGHT // 1.1) - 32
LINE_COLOR = (255, 255, 0)
LINE_THICKNESS = 5
SWITCH_TIMEOUT = 20

# Sensitivity control
sensitivity = 1.0  # Default sensitivity

# Setup Pygame Display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)

# Load and Pre-Scale Background Images
background_folder = "/home/pi/Projects/cava-pygame/backgrounds"
background_images = sorted(glob.glob(os.path.join(background_folder, "*.png")))

if not background_images:
    raise FileNotFoundError("No background images found in 'backgrounds/' folder!")

backgrounds = [pygame.transform.scale(pygame.image.load(img), (SCREEN_WIDTH, SCREEN_HEIGHT)) for img in background_images]
bg_index = 0
last_switch_time = time.time()

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

while running:
    if bg_index in [1, 2] and time.time() - last_switch_time > SWITCH_TIMEOUT:
        bg_index = 0
        last_switch_time = time.time()

    screen.blit(backgrounds[bg_index], (0, 0))

    if bg_index == 0:
        with data_lock:
            local_cava_data = cava_data[:]

        BARS = len(local_cava_data)
        POINT_SPACING = SCREEN_WIDTH / (BARS - 1)
        center_y = SCREEN_HEIGHT // 2

        upper_wave = [
            (i * POINT_SPACING, center_y - max(2, min(int(val * sensitivity), MAX_BAR_HEIGHT)) // 2)
            for i, val in enumerate(local_cava_data)
        ]
        lower_wave = [(x, 2 * center_y - y) for x, y in upper_wave]

        if len(upper_wave) > 1:
            pygame.draw.lines(screen, LINE_COLOR, False, upper_wave, LINE_THICKNESS)
            pygame.draw.lines(screen, LINE_COLOR, False, lower_wave, LINE_THICKNESS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if pygame.K_1 <= event.key <= pygame.K_9:
                key_number = event.key - pygame.K_1
                if key_number < len(backgrounds):
                    bg_index = key_number
                    last_switch_time = time.time()
            elif event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_UP:
                sensitivity = min(sensitivity + 0.1, 5.0)
                print(f"Sensitivity increased to {sensitivity:.1f}")
            elif event.key == pygame.K_DOWN:
                sensitivity = max(sensitivity - 0.1, 0.1)
                print(f"Sensitivity decreased to {sensitivity:.1f}")

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
