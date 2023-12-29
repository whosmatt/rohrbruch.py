import argparse
import socket
import threading
import time
import random
import math
from itertools import product
from PIL import Image

def gen_hex(r, g, b):
  if (r == g == b == 0):
    return "0"
  hexv = f'%02x%02x%02x' % (r, g, b)
  return hexv.lstrip("0")

def gen_pixels(pixels):
  commands = []
  for x, y in pixels:
    r, g, b, a = image.getpixel((x, y))
    if a:
      commands.append(f"PX {x} {y} {gen_hex(r,g,b)}\n")
  return commands


def gen_blocks(image):
  commands = []
  block_size = args.blocksize
  for block_x in range(0, image.width, block_size):
    for block_y in range(0, image.height, block_size):
      block_has_data = False
      offset_x = block_x
      offset_y = block_y
      block_commands = ""
      block_commands += f"OFFSET {offset_x} {offset_y}\n"
      pixels = [(x, y) for x, y in random.sample(list(product(range(block_x, block_x + block_size), range(block_y, block_y + block_size))), block_size * block_size)]
      for x, y in pixels:
        if 0 <= x < image.width and 0 <= y < image.height:
          r, g, b, a = image.getpixel((x, y))
          if a:
            block_has_data = True
            block_commands += f"PX {x - block_x} {y - block_y} {gen_hex(r,g,b)}\n"
          
      if block_has_data:
        commands.append(block_commands)
  return commands

def send_pixels(commands):
  global run
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
  sock.connect((args.host, args.port))
  while not run:
    time.sleep(5)

  while run:
    try:
      sock.send(''.join(commands).encode())
    except socket.error as e:
      try:
        sock.close()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        time.sleep(5)
        while(run):
          try:
            sock.connect((args.host, args.port))
            break
          except TimeoutError:
            print(f"Thread {threading.get_ident()} failed to reconnect, retrying in 5s.")
        print(f"Thread {threading.get_ident()} lost and reestablished connection ({e}).")
      except Exception as e:
        print(f"Thread {threading.get_ident()} died: {e}")
  print(f"Stopping Thread: {threading.get_ident()}", end="\r")
  sock.close()  

def start ():
  global run
  run = False
  commands_len = 0
  for command in commands:
    commands_len += len(command)
  blocks_len = 0
  for block_commands in blocks:
    blocks_len += len(block_commands)
  block_efficiency = round(blocks_len / commands_len, 2)
  print(f"Starting job:\n commands bytes: {commands_len} \n blocks bytes: {blocks_len} \n total blocks: {len(blocks)}\n block efficiency:{block_efficiency}")

  global threads 
  threads = []

  if (block_efficiency >= 1 or args.force_global) and not args.force_tiled:
    print("Choosing global draw mode")
    if args.connections is None:
      num_threads = len(blocks)
    else:
      num_threads = args.connections
    print(f"{num_threads} threads running with 1 connection per thread...")
    for i in range(num_threads):
      start = i * len(commands) // num_threads
      end = (i + 1) * len(commands) // num_threads
      t = threading.Thread(target=send_pixels, args=(commands[start:end],))
      threads.append(t)
      t.start()
      print(f"Spawning threads: {i}", end="\r")

  else: 
    print(f"Choosing tiled offset draw mode due to better block efficiency")
    if args.connections is None or args.connections > len(blocks):
      args.connections = len(blocks)
    
    merged_blocks = []

    firstblock = 0
    for i in range(args.connections):
      lastblock = firstblock + math.floor(len(blocks)/args.connections)
      merged_block = ''.join(blocks[firstblock:lastblock])
      merged_blocks.append(merged_block)
      firstblock = lastblock

    if firstblock < len(blocks) - 1:
      missing_blocks = ''.join(blocks[firstblock:])
      merged_blocks[0] += missing_blocks

    print(f"Starting {len(merged_blocks)} connections...")

    for i, block_commands in enumerate(merged_blocks):
      t = threading.Thread(target=send_pixels, args=(block_commands,))
      threads.append(t)
      t.start()
      print(f"Spawning threads: {i}", end="\r")
  run = True

def stop ():
  global run
  run = False
  try:
    for t in threads:
      t.join()
  except KeyboardInterrupt:
    for t in threads:
      t.join(timeout=0)
    

def generate():
  global image
  global pixels
  global commands
  global blocks
  image = Image.open(args.image).convert("RGBA")
  print("loaded image")
  if (args.norandom):
    pixels = [(x,y) for x in range(image.width) for y in range(image.height)]
  else:
    pixels = [(x, y) for x, y in random.sample(list(product(range(image.width), range(image.height))), image.width * image.height)]
  print("generated pixelmap")
  commands = gen_pixels(pixels)
  print("generated commands")
  blocks = gen_blocks(image)
  print("generated blocks")

parser = argparse.ArgumentParser(description="fluts pixels, automatically calculating the most efficient method, comically cpu intensive")
parser.add_argument("host", type=str)
parser.add_argument("port", nargs="?", type=int, default=1234)
parser.add_argument("--image", "-i", type=str, required=True, help="path to image")
modeSwitch = parser.add_mutually_exclusive_group()
modeSwitch.add_argument("--global", "-g", dest="force_global", action="store_true", help="force global mode")
modeSwitch.add_argument("--tiled", "-t", dest="force_tiled", action="store_true", help="force tiled mode")
parser.add_argument("--connections", "-c", type=int, help="number of connections/threads, ignored in tiled mode")
parser.add_argument("--blocksize", "-b", default=100, type=int, help="tiled mode block size in px, values 100 and 10 are most efficient. smaller blocks => more connections")
parser.add_argument("--norandom", "-nr", action="store_true", help="disable random order")

args = parser.parse_args()

generate()
start()
while True:
  try:
    imageInput = input("Enter a new path to set a new image or enter nothing to reload the set image, CTRL+C to quit\n")
    if imageInput == "":
      pass
    else:
      args.image = imageInput.strip()
  except KeyboardInterrupt: 
    print("Killing connections...")
    stop()
    break
  else:
    print("Closing connections and stopping threads...")
    stop()
    print("Rebuilding commands...")
    generate()
    print("Restarting threads")
    start()
