# rohrbruch.py
horrible but superior pixelflut client for servers that accept many connections

by implementing the often supported offset command to send relative coordinates, effective bandwidth is reduced by ~20%, allowing significantly higher throughput. this implementation uses one connection per block, a full 720p image will already need over 100 connections. A different approach combining multiple blocks into one connection would be feasible, but requires frequent re-sending of the offset command and has not been implemented. 

the color format is optimized by truncating any trailing zeroes and ignoring pixels that have full transparency. 

## Usage
` python3 .\rohrbruch.py --image img.png --tiled --blocksize 100 --connections 16 --norandom 123.123.123.123 1337`

- `--image` path to image compatible with PIL (most formats, transparency supported)
- `--global | --tiled` global mode works similar to other pixelflut clients and is used for servers with low available connections
- `--blocksize uint` only used in tiled mode, `100` would result in 100x100px blocks. values other than 10, 100, 1000 don't make a lot of sense. 100 is recommended. lower values result in more blocks and more connections. with blocksize=10, large images will produce an absurd amount of connections. 10 is best used with small images or lots of alpha. 
- `--connections uint` only used in global mode. determines the amount of parallel connections used to draw the image
- `--norandom` by default pixels are drawn in random order for a better visual effect. use this flag to disable randomization.

Image size and offset are not implemented. The intended workflow is to create a transparent image with the full canvas size and edit/save this image to position and scale elements. 
