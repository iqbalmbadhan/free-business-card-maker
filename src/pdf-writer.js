  // Minimal PDF writer: one full-bleed JPEG per page, with TrimBox/BleedBox set for print shops.
  // pages: [{ jpeg: Uint8Array, w: pixelWidth, h: pixelHeight }]; sizes in mm.
  function buildPdf(pages, pageWmm, pageHmm, bleedMm, title) {
    const enc = new TextEncoder();
    const pt = (mm) => (mm * 72 / 25.4);
    const f = (n) => (Math.round(n * 1000) / 1000).toString();
    const W = pt(pageWmm), H = pt(pageHmm), B = pt(bleedMm);
    const parts = []; const offsets = []; let pos = 0;
    const push = (x) => { const bytes = typeof x === "string" ? enc.encode(x) : x; parts.push(bytes); pos += bytes.length; };
    const pdfText = (s) => {
      let hex = "FEFF";
      for (const ch of String(s)) {
        const cp = ch.codePointAt(0);
        const units = cp > 0xFFFF ? [0xD800 + ((cp - 0x10000) >> 10), 0xDC00 + ((cp - 0x10000) & 0x3FF)] : [cp];
        units.forEach(u => { hex += u.toString(16).toUpperCase().padStart(4, "0"); });
      }
      return "<" + hex + ">";
    };
    const n = pages.length;
    // object numbers: 1 catalog, 2 pages, 3 info, then per page: page, contents, image
    const pageObj = (i) => 4 + i * 3, contObj = (i) => 5 + i * 3, imgObj = (i) => 6 + i * 3;
    const total = 3 + n * 3;
    const obj = (num, body) => { offsets[num] = pos; push(`${num} 0 obj\n${body}\nendobj\n`); };

    push("%PDF-1.4\n"); push(new Uint8Array([0x25, 0xE2, 0xE3, 0xCF, 0xD3, 0x0A]));
    obj(1, "<< /Type /Catalog /Pages 2 0 R >>");
    obj(2, `<< /Type /Pages /Kids [${pages.map((_, i) => pageObj(i) + " 0 R").join(" ")}] /Count ${n} >>`);
    obj(3, `<< /Title ${pdfText(title)} /Creator (Business Card Maker - AiInfos) /Producer (Business Card Maker - AiInfos) >>`);
    pages.forEach((p, i) => {
      const box = `[0 0 ${f(W)} ${f(H)}]`;
      const trim = `[${f(B)} ${f(B)} ${f(W - B)} ${f(H - B)}]`;
      obj(pageObj(i), `<< /Type /Page /Parent 2 0 R /MediaBox ${box} /BleedBox ${box} /TrimBox ${trim} /Resources << /XObject << /Im0 ${imgObj(i)} 0 R >> >> /Contents ${contObj(i)} 0 R >>`);
      const content = `q ${f(W)} 0 0 ${f(H)} 0 0 cm /Im0 Do Q`;
      obj(contObj(i), `<< /Length ${enc.encode(content).length} >>\nstream\n${content}\nendstream`);
      offsets[imgObj(i)] = pos;
      push(`${imgObj(i)} 0 obj\n<< /Type /XObject /Subtype /Image /Width ${p.w} /Height ${p.h} /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length ${p.jpeg.length} >>\nstream\n`);
      push(p.jpeg); push("\nendstream\nendobj\n");
    });
    const xref = pos;
    let x = `xref\n0 ${total + 1}\n0000000000 65535 f \n`;
    for (let i = 1; i <= total; i++) x += String(offsets[i]).padStart(10, "0") + " 00000 n \n";
    push(x);
    push(`trailer\n<< /Size ${total + 1} /Root 1 0 R /Info 3 0 R >>\nstartxref\n${xref}\n%%EOF\n`);
    const out = new Uint8Array(pos); let o = 0;
    parts.forEach(b => { out.set(b, o); o += b.length; });
    return out;
  }
