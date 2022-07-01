import json
import random
from io import BytesIO
import base64
import numpy as np
from PIL import Image, ImageOps
import timeit # performance testing

import LogoBinarizer as lb

SENSIBILITY = 5
NOISE = 30

def get_tile_dims(x,y, min=25, max=50):
  #n_tile_x = random.randint(min, max)
  #n_tile_y = round(n_tile_x*(y/x))
  #return n_tile_x, n_tile_y
  return 50, 50
  
def get_tile_from_coordinates(x, y, mask, tile_dim):
  # get range for x coordinate of corresponding tile 
  x_tile = int(np.floor(x/tile_dim))
  x_tile_range_lower = tile_dim * x_tile
  x_tile_range_upper = x_tile_range_lower + tile_dim

  # get range for y coordinate of corresponding tile 
  y_tile = int(np.floor(y/tile_dim))
  y_tile_range_lower = tile_dim * y_tile
  y_tile_range_upper = y_tile_range_lower + tile_dim

  tile = mask[y_tile_range_lower:y_tile_range_upper, x_tile_range_lower:x_tile_range_upper]

  return tile

def adjust_coordinates(x, sums, threshold, tile_dim):
  new_x = x
  if sums[1] <= threshold:
    new_x -=2
  elif sums[0] <= threshold:
    new_x -=1
  if sums[tile_dim-2] <= threshold:
    new_x +=2
  elif sums[tile_dim-1] <= threshold:
    new_x +=1

  return new_x
  
def campionate(img, tile_dim=5):
  # constants
  overlap_noise = True
  separate_movements = False 
  disable_big = True 
  enable_rotation = False

  # randomly generate tile dimensions (between x and y) keeping proportions
  n_tile_w, n_tile_h = get_tile_dims(img.width, img.height)
  if n_tile_h > 60:
    n_tile_h, n_tile_w = get_tile_dims(img.height, img.width)

  # calculate new dims from tile size and number of tiles  
  new_h = tile_dim * n_tile_h
  new_w = tile_dim * n_tile_w

  # resize
  img = img.resize((new_h, new_w))

  # binarize (False/0 => trasparent)
  mask = np.array(img) > 200

  # if the non-transparent pixels are more than the half
  if mask.sum() > mask.size/2:
    mask = mask^1 # invert binary mask

  # count non-transparent pixels in each tile
  slicesx = np.arange(0, mask.shape[0], tile_dim)
  pixel_count = np.add.reduceat(mask, slicesx, axis=0)
  slicesy = np.arange(0, mask.shape[1], tile_dim)
  pixel_count = np.add.reduceat(pixel_count, slicesy, axis=1)

  # condition 1 => filled with black pixels (1)
  full_black_val = tile_dim * tile_dim
  xs, ys = np.where(pixel_count == full_black_val)
  # map each tile to the central pixel of the original image
  xs = xs * tile_dim + (np.ceil(tile_dim/2))
  ys = ys * tile_dim + (np.ceil(tile_dim/2))
  final_coordinates = list(zip(xs, ys))

  # condition 2 => above min_val & adjust based on tile distribution
  min_val = full_black_val/3
  # note that we also check only the pixels that didn't satisfy condition 1
  xs, ys = np.where((pixel_count > min_val) & (pixel_count < full_black_val))
  # map each tile to the central pixel of the original image
  xs = xs * tile_dim + (np.ceil(tile_dim/2))
  ys = ys * tile_dim + (np.ceil(tile_dim/2))
  # depending on where the transparent pixels are in the tile,
  # move the coordinates
  to_adjust_coordinates = np.array(list(zip(xs, ys))) 
  threshold = tile_dim/3
  # for each point to adjust
  for (x, y) in to_adjust_coordinates:
    # retrieve the corresponding tile and sums over cols and rows
    tile = get_tile_from_coordinates(x, y, mask, tile_dim)
    col_sums = tile.sum(axis=0)
    row_sums = tile.sum(axis=1)

    # adjust the coordinates based on the row and col sums
    new_x = adjust_coordinates(x, row_sums, threshold, tile_dim)
    new_y = adjust_coordinates(y, col_sums, threshold, tile_dim)
    final_coordinates.append((new_x, new_y))

  return np.array(final_coordinates), new_h, new_w

def get_c(val, sol_x, sol_y, offset):
  m1 = random.randint(-10000*SENSIBILITY, 10000*SENSIBILITY)/100000
  m2 = random.randint(-10000*SENSIBILITY, 10000*SENSIBILITY)/100000
  c = round(val-sol_y*m1-sol_x*m2)+offset
  return m2, m1, int(c)
  
# convert list of coordinates to riki_string  
def to_riki_string(cs):
  final_riki = ""
  for t in cs:
    riki_string = "@{} {} {} {} {} {}".format(int(t[0]*100000), int(t[1]*100000), t[2], int(t[3]*100000), int(t[4]*100000), t[5])
    final_riki += riki_string 
  return final_riki

def lambda_handler(event, context):
  try:
    base64_img = event['img_base64']
    
    # base64 to PIL image
    start = timeit.default_timer() # TEST
    binary = base64.b64decode(base64_img)
    img = Image.open(BytesIO(binary))
    
    # binarization 
    start_bin = timeit.default_timer() # TEST
    img = np.array(img)
    logoBin = lb.LogoBinarizer()
    img = logoBin.binarize(img)
    img = Image.fromarray(img)
    end_bin = timeit.default_timer() # TEST
    overall_bin = end_bin - start_bin # TEST
    
    # get captcha from image
    start_camp = timeit.default_timer() # TEST
    star_coordinates, h, w = campionate(img)
    end_camp = timeit.default_timer() # TEST
    overall_camp = end_camp - start_camp # TEST
    
    # calculate cs
    start_cs = timeit.default_timer() # TEST
    offset_x = random.randint(0, 300-w)
    offset_y = random.randint(0, 300-h)
    sol_x = random.randint(10, 290)
    sol_y = random.randint(10, 290)
    cs = [get_c(x, sol_x, sol_y, offset_x) + 
          get_c(y, sol_x, sol_y, offset_y) for x,y in star_coordinates]
    end_cs = timeit.default_timer() # TEST
    overall_cs = end_cs - start_cs # TEST
          
    # add noise
    start_noise = timeit.default_timer() # TEST
    n_noise = int(star_coordinates.shape[0]*NOISE/100)
    noise_coordinates = [(random.randint(0,300), random.randint(0,300)) for _ in range(n_noise)]
    cs_noise = [get_c(x, random.randint(0,300), random.randint(0,300), 0) + 
            get_c(y, random.randint(0,300), random.randint(0,300), 0) for x,y in noise_coordinates]
    print("n stars: ", len(cs)) # TEST
    cs = cs + cs_noise
    print("n stars + noisy: ", len(cs)) # TEST
    end_noise = timeit.default_timer() # TEST
    overall_noise = end_noise - start_noise # TEST
    
    # get riki string
    start_riki = timeit.default_timer() # TEST
    stars = to_riki_string(cs)
    end_riki = timeit.default_timer() # TEST
    overall_riki = end_riki - start_riki # TEST
    
    end = timeit.default_timer() # TEST
    overall = end-start
    print("overall time: ", overall) # TEST
    print("preprocess: ", overall_bin, overall_bin/overall)
    print("decomposition: ", overall_camp, overall_camp/overall)
    print("trajectory: ", overall_cs, overall_cs/overall)
    print("noise: ", overall_noise, overall_noise/overall)
    print("riki: ", overall_riki, overall_riki/overall)
    print("- :", overall-overall_bin)
    
    statusCode = 200
    response_body = {
      'stars': stars,
      'sol_x': sol_x,
      'sol_y': sol_y
    }
  
  except Exception as err:
    statusCode = 500
    response_body = {'error': 'get_captcha: ' + str(err)}

  return {
      'statusCode': statusCode,
      'body': response_body
  }