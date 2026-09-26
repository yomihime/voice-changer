// Extracted declaration from ../main-ui.js:35068-35123.
// Navigation/reference excerpt; shared bundle dependencies are NOT imported.
// Edit ../main-ui.js for a runnable change. This is not original TS/TSX source.
class FileUploaderClient {
  #e;
  enableFlatPath = !1;
  constructor() {
    this.#e = "";
  }
  setBaseUrl = (C) => {
    (C.endsWith("/") && (C = C.slice(0, -1)), (this.#e = C));
  };
  setEnableFlatPath = (C) => {
    this.enableFlatPath = C;
  };
  generatePath = (C) =>
    this.enableFlatPath ? C[0] + C.slice(1).replace(/\//g, "_") : C;
  uploadFile = async (C, E, w) => {
    const R = this.#e + this.generatePath("/api/uploader/upload_file_chunk");
    w(0, !1);
    const _ = 1024 * 1024;
    let x = 0;
    const T = E.size,
      A = C + E.name,
      O = Math.ceil(T / _);
    for (;;) {
      const H = [];
      for (let ee = 0; ee < 10 && !(x * _ >= T); ee++) {
        const te = E.slice(x * _, (x + 1) * _),
          ie = new Promise((ne) => {
            const ae = new FormData();
            (ae.append("file", new Blob([te])),
              ae.append("filename", `${A}`),
              ae.append("index", `${x}`));
            const se = new Request(R, { method: "POST", body: ae });
            fetch(se).then(async (ce) => {
              (console.log(await ce.text()), ne());
            });
          });
        ((x += 1), H.push(ie));
      }
      if ((await Promise.all(H), x * _ >= T)) break;
      w(Math.floor((x / (O + 1)) * 100), !1);
    }
    return O;
  };
  concatUploadedFile = async (C, E) => {
    const w =
      this.#e + this.generatePath("/api/uploader/concat_uploaded_file_chunk");
    await new Promise((R) => {
      const _ = new FormData();
      (_.append("filename", C), _.append("filename_chunk_num", "" + E));
      const x = new Request(w, { method: "POST", body: _ });
      fetch(x).then(async (T) => {
        (console.log(await T.text()), R());
      });
    });
  };
}
