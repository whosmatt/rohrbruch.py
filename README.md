# rohrbruch.py
horrible but superior pixelflut client for servers that implement the offset command (often not entirely documented)

by implementing the often supported offset command to send relative coordinates, effective bandwidth is reduced by ~20%, allowing significantly higher throughput. this implementation uses one connection per block, a full 720p image will already need over 100 connections. A different approach combining multiple blocks into one connection would be feasible, but requires frequent re-sending of the offset command and has not been implemented. 

the color format is optimized by truncating any trailing zeroes and ignoring pixels that have full transparency. 

## Usage
` python3 rohrbruch.py --image img.png --connections 16 123.123.123.123 1337`

- `--image` path to image compatible with PIL (most formats, transparency supported)
- `--global | --tiled` global mode works similar to other pixelflut clients and is used for servers with low available connections. chosen automatically (by efficiency) if not provided. 
- `--blocksize uint` only used in tiled mode, `100` would result in 100x100px blocks. values other than 10, 100, 1000 don't make a lot of sense. 10 will give maximum efficiency, but make sure to limit connections to a reasonable value. 
- `--connections uint` determines the amount of parallel connections used to draw the image. defaults to a lot of connections (1 per block, also in global draw mode) when not provided. automatically capped at 1 connection per block in tiled mode. 
- `--norandom` by default pixels are drawn in random order for a better visual effect. use this flag to disable randomization.
- `host` host ip or domain
- `port` defaults to 1234 if not provided

Image size and offset are not implemented. The intended workflow is to create a transparent image with the full canvas size and edit/save this image to position and scale elements. 
