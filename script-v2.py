
import os, glob, json

root = '/storage/emulated/0/ascii-art2'

with open(os.path.join(root, 'ascii-dict-v4.json')) as d:
	ad = json.load(d)

subject = max(glob.glob(os.path.join(root, 'subjects', '*')), key=os.path.getmtime)
title = input('Title: ')
caption = input('Caption: ')

from PIL import Image, ImageFont, ImageDraw
import numpy as np, math

adk, adv = ad.keys(), np.array(list(ad.values()))

fs = 16 # font size
fr = 3 / 5 #font aspect ratio
fw, fh = math.ceil(fs * fr), fs #font width, font height
_4K = 1_920 #frame size
Fw, Fh = 360, 640# 800, 1422#1080, 1920

with Image.open(subject) as im:
	
	w, h = im.size
	w = Fh / h * w
	h = Fh
	
	w, h = math.ceil(w), math.ceil(h)
	rw, rh = Fw // fw, Fh // fh
	L = Fw % w // 2
	
	arr = np.array(im.resize((w, h), Image.NEAREST).crop((
		L,
		0,
		L + rw * fw,
		rh * fh
	)).resize((rw * 2, rh * 2), Image.BOX).convert('L'))

_0 = np.min(arr)
_100 = np.max(arr) - _0

r = np.full((rh, rw), '', dtype=object)

import base64
from threading import Thread
from concurrent.futures import ThreadPoolExecutor
from time import sleep
from pathvalidate import sanitize_filename

p = 0
e = {}

def progress():
	while True:
		print('%d%% (%d/%d) completed' % (round(p / r.size * 100), p, r.size))
		if p == r.size:
			break
		sleep(1)

def worker(x, y, xx, yy):
	b = arr[yy : yy + 2, xx : xx + 2]
	k = bytes(b)
	if k in e:
		r[y][x] = e[k]
		return
	dv = [np.linalg.norm((b - _0) / _100 - c) for c in adv]
	rr = dict(zip(dv, adk))[min(dv)]
	r[y][x] = rr
	e[k] = rr

def proxy(args):
	try:
		worker(*args)
	except Exception as err:
		print(err)
	global p
	p += 1

Thread(target=progress).start()

print('generating ascii art...')
with ThreadPoolExecutor(max_workers=os.cpu_count()) as ex:
	ex.map(proxy, [(x, y, x * 2, y * 2) for y in range(rh) for x in range(rw)])

print('creating image...')

fn = '%s-%s.png' % (sanitize_filename(title), base64.urlsafe_b64encode(os.urandom(3)).decode())

monospace = ImageFont.truetype(os.path.join(root, 'RobotoMono-Regular.ttf'), 16 * 3)
m = 0#8
lw, lh = monospace.getbbox(''.join(r[0]))[2:]
preview = Image.new('L', (lw + m * 2, lh * rh + m * 2), 0)
dr = ImageDraw.Draw(preview)
for l in range(len(r)):
	dr.text((m, m + l * lh), ''.join(r[l]), font=monospace, fill=204)
preview.save(os.path.join(root, fn), format='PNG', compress_level=0, optimize=True)

exit()
print('preview saved to', fn)

print('creating html...')

output = '\n'.join(''.join(l) for l in r)

fn = '%s-%s.html' % (sanitize_filename(title), base64.urlsafe_b64encode(os.urandom(3)).decode())

with open(os.path.join(root, fn), 'w') as o:
	
	title_html = html.escape(title)
	output_html = html.escape(output)
	caption_html = html.escape(caption)
	
	o.write('''<!DOCTYPE html>
<html lang="en">
<head>
<base href="https://ldaelo.github.io/ascii-art/">
<meta charset="UTF-8">
<title>ASCII Art: %s</title>
<link rel="stylesheet" href="styles.css">
</head>
<body>
<figure>
  <pre role="img">%s</pre>
  <figcaption>
    <h1>%s</h1>
    <h2>%s</h2>
    <p>donate via PayPal (<a href="https://www.paypal.me/paelom">paelom</a>) or GCash (09076598998 Paelo Moldes)</p>
    <hr>
    <div class="license">
      <p>This work is licensed under the <a href="https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode.en">CC BY-NC-ND 4.0 License</a>.</p>
      <a href="https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode.en"><img src="by-nc-nd.png" alt="CC BY-NC-ND 4.0 License"></a>
    </div>
  </figcaption>
</figure>
</body>
</html>''' % (title_html, output_html, title_html, caption_html))

print('html saved to', fn)