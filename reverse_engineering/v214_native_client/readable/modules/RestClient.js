// Extracted declaration from ../main-ui.js:35149-35264.
// Navigation/reference excerpt; shared bundle dependencies are NOT imported.
// Edit ../main-ui.js for a runnable change. This is not original TS/TSX source.
class RestClient {
  #e;
  constructor() {
    this.#e = "";
  }
  setBaseUrl = (C) => {
    (C.endsWith("/") && (C = C.slice(0, -1)), (this.#e = C));
  };
  execFetch = async (C, E = "json") =>
    new Promise((w) => {
      fetch(C)
        .then(async (R) => {
          if (R.ok) {
            let _;
            (E === "blob" ? (_ = await R.blob()) : (_ = await R.json()),
              w(new Ok(_)));
          } else {
            const _ = await R.text();
            try {
              const x = JSON.parse(_);
              if (x.error != null) {
                const T = JSON.parse(x.error),
                  A = {
                    type: "ERR_HTTP_EXCEPTION",
                    status: R.status,
                    statusText: R.statusText,
                    code: T.code,
                    reason: T.reason,
                    action: T.action,
                    detail: T.detail,
                  };
                w(new Err(A));
              } else {
                const T = {
                  type: "ERR_HTTP_EXCEPTION",
                  status: R.status,
                  statusText: R.statusText,
                  code: x.code,
                  reason: "no detail",
                  action: "no action",
                  detail: x.detail,
                };
                w(new Err(T));
              }
            } catch (x) {
              const T = {
                type: "ERR_HTTP_EXCEPTION",
                status: R.status,
                statusText: R.statusText,
                code: -1,
                reason: `JSON parse error: ${x}`,
                action: "Check server response",
                detail: _.substring(0, 200),
              };
              w(new Err(T));
            }
          }
        })
        .catch((R) => {
          console.error(R);
          const _ = {
            type: "ERR_HTTP_EXCEPTION",
            status: 0,
            statusText: "",
            code: -1,
            reason: `${R}`,
            action: "",
            detail: null,
          };
          w(new Err(_));
        });
    });
  getRequest = async (C, E = "json") => {
    let w = C.startsWith("/") ? `${this.#e}${C}` : `${this.#e}/${C}`;
    const R = new Request(w, { method: "GET" }),
      _ = await this.execFetch(R, E);
    if (!_.isOk()) throw _.get();
    return _.get();
  };
  postRequest = async (C, E, w = "json") => {
    let R = C.startsWith("/") ? `${this.#e}${C}` : `${this.#e}/${C}`;
    const _ = new Request(R, {
        method: "POST",
        body: JSON.stringify(E),
        headers: { "Content-Type": "application/json" },
      }),
      x = await this.execFetch(_, w);
    if (!x.isOk()) throw x.get();
    return x.get();
  };
  putRequest = async (C, E, w = "json") => {
    let R = C.startsWith("/") ? `${this.#e}${C}` : `${this.#e}/${C}`;
    const _ = new Request(R, {
        method: "PUT",
        body: JSON.stringify(E),
        headers: { "Content-Type": "application/json" },
      }),
      x = await this.execFetch(_, w);
    if (!x.isOk()) throw x.get();
    return x.get();
  };
  deleteRequest = async (C, E, w = "json") => {
    let R = C.startsWith("/") ? `${this.#e}${C}` : `${this.#e}/${C}`,
      _;
    E != null
      ? (_ = new Request(R, {
          method: "DELETE",
          body: JSON.stringify(E),
          headers: { "Content-Type": "application/json" },
        }))
      : (_ = new Request(R, { method: "DELETE" }));
    const x = await this.execFetch(_, w);
    if (!x.isOk()) throw x.get();
    return x.get();
  };
}
