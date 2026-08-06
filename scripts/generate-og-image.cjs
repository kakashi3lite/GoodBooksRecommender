/**
 * 🖼️ OG Image Generator
 * Chain-of-Thought: Produces a 1200×630 PNG social preview card (brand gradient)
 * using only Node built-ins (zlib) — no native deps. Social platforms (Twitter/X,
 * Facebook, LinkedIn) require raster PNG/JPG for og:image.
 *
 * Run: node scripts/generate-og-image.js
 */

const zlib = require('zlib')
const fs = require('fs')
const path = require('path')

const W = 1200
const H = 630

// Brand colors (match tailwind/design system)
const C1 = { r: 29, g: 78, b: 216 } // blue-700
const C2 = { r: 124, g: 58, b: 237 } // violet-600

// ---- PNG encoding helpers ------------------------------------------------

const crcTable = (() => {
  const t = new Uint32Array(256)
  for (let n = 0; n < 256; n++) {
    let c = n
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1
    t[n] = c >>> 0
  }
  return t
})()

const crc32 = (buf) => {
  let c = 0xffffffff
  for (let i = 0; i < buf.length; i++) c = crcTable[(c ^ buf[i]) & 0xff] ^ (c >>> 8)
  return (c ^ 0xffffffff) >>> 0
}

const chunk = (type, data) => {
  const len = Buffer.alloc(4)
  len.writeUInt32BE(data.length)
  const typeBuf = Buffer.from(type, 'ascii')
  const crcBuf = Buffer.alloc(4)
  crcBuf.writeUInt32BE(crc32(Buffer.concat([typeBuf, data])))
  return Buffer.concat([len, typeBuf, data, crcBuf])
}

const buildPng = (width, height, rgba) => {
  const sig = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a])
  const ihdr = Buffer.alloc(13)
  ihdr.writeUInt32BE(width, 0)
  ihdr.writeUInt32BE(height, 4)
  ihdr[8] = 8 // bit depth
  ihdr[9] = 6 // color type RGBA
  ihdr[10] = 0
  ihdr[11] = 0
  ihdr[12] = 0

  const stride = width * 4
  const raw = Buffer.alloc((stride + 1) * height)
  for (let y = 0; y < height; y++) {
    raw[y * (stride + 1)] = 0 // filter: none
    rgba.copy(raw, y * (stride + 1) + 1, y * stride, (y + 1) * stride)
  }
  const idat = zlib.deflateSync(raw, { level: 9 })
  return Buffer.concat([sig, chunk('IHDR', ihdr), chunk('IDAT', idat), chunk('IEND', Buffer.alloc(0))])
}

// ---- Render the gradient -------------------------------------------------

const px = Buffer.alloc(W * H * 4)
for (let y = 0; y < H; y++) {
  for (let x = 0; x < W; x++) {
    const t = (x + y) / (W + H) // diagonal progress 0..1
    const i = (y * W + x) * 4
    px[i] = Math.round(C1.r + (C2.r - C1.r) * t)
    px[i + 1] = Math.round(C1.g + (C2.g - C1.g) * t)
    px[i + 2] = Math.round(C1.b + (C2.b - C1.b) * t)
    // Subtle vignette at the bottom for depth
    const v = Math.max(0, (y - H * 0.55) / (H * 0.45))
    px[i] = Math.round(px[i] * (1 - v * 0.18))
    px[i + 1] = Math.round(px[i + 1] * (1 - v * 0.18))
    px[i + 2] = Math.round(px[i + 2] * (1 - v * 0.22))
    px[i + 3] = 255
  }
}

const outDir = path.join(__dirname, '..', 'public')
fs.mkdirSync(outDir, { recursive: true })
const outPath = path.join(outDir, 'og-cover.png')
fs.writeFileSync(outPath, buildPng(W, H, px))
console.log(`✅ Generated ${outPath} (${W}x${H}, ${(fs.statSync(outPath).size / 1024).toFixed(0)} KB)`)
